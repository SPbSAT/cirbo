#pragma once

#include <map>
#include <string>
#include <filesystem>
#include <iostream>
#include <vector>

#include <mockturtle/mockturtle.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/io/write_bench.hpp>
#include <kitty/constructors.hpp>
#include <kitty/dynamic_truth_table.hpp>
#include <lorina/bench.hpp>

#include "mockturtle/traits.hpp"


/**
 * Mockturtle bench_reader with public `signals` field (for mapping gates between circuit and klut-network)
 */
namespace mockturtle {

template<typename Ntk>
class public_bench_reader : public lorina::bench_reader
{
public:
  explicit public_bench_reader( Ntk& ntk ) : _ntk( ntk )
  {
    static_assert( is_network_type_v<Ntk>, "Ntk is not a network type" );
    static_assert( has_create_pi_v<Ntk>, "Ntk does not implement the create_pi function" );
    static_assert( has_create_po_v<Ntk>, "Ntk does not implement the create_po function" );
    static_assert( has_get_constant_v<Ntk>, "Ntk does not implement the get_constant function" );
    static_assert( has_create_node_v<Ntk>, "Ntk does not implement the create_node function" );
    signals["gnd"] = _ntk.get_constant( false );
    signals["vdd"] = _ntk.get_constant( true );
  }

  ~public_bench_reader()
  {
    for ( auto const& o : outputs )
    {
      _ntk.create_po( signals[o] );
    }
  }

  void on_input( const std::string& name ) const override
  {
    signals[name] = _ntk.create_pi();
    if constexpr ( has_set_name_v<Ntk> )
    {
      _ntk.set_name( signals[name], name );
    }
  }

  void on_output( const std::string& name ) const override
  {
    if constexpr ( has_set_output_name_v<Ntk> )
    {
      _ntk.set_output_name( outputs.size(), name );
    }
    outputs.emplace_back( name );
  }

  void on_assign( const std::string& input, const std::string& output ) const override
  {
    signals[output] = signals.at( input );
  }

  void on_gate( const std::vector<std::string>& inputs, const std::string& output, const std::string& type ) const override
  {
    if ( type.size() > 2 && std::string_view( type ).substr( 0, 2 ) == "0x" && inputs.size() <= 6u )
    {
      /* modern-style gate definition */
      kitty::dynamic_truth_table tt( static_cast<int>( inputs.size() ) );
      kitty::create_from_hex_string( tt, type.substr( 2 ) );

      std::vector<signal<Ntk>> input_signals;
      for ( const auto& i : inputs )
        input_signals.push_back( signals[i] );

      signals[output] = _ntk.create_node( input_signals, tt );
    }
    else
    {
      /* old-style gate definition */
      std::vector<signal<Ntk>> input_signals;
      for ( const auto& i : inputs )
        input_signals.push_back( signals[i] );

      kitty::dynamic_truth_table tt( static_cast<int>( inputs.size() ) );

      std::vector<kitty::dynamic_truth_table> vs( inputs.size(), tt );
      for ( auto i = 0u; i < inputs.size(); ++i )
        kitty::create_nth_var( vs[i], i );

      if ( type == "NOT" )
      {
        assert( inputs.size() == 1u );
        tt = ~vs.at( 0u );
      }
      else if ( type == "BUFF" )
      {
        assert( inputs.size() == 1u );
        tt = vs.at( 0u );
      }
      else if ( type == "AND" )
      {
        tt = vs.at( 0u );
        for ( auto i = 1u; i < inputs.size(); ++i )
          tt &= vs.at( i );
      }
      else if ( type == "NAND" )
      {
        tt = vs.at( 0u );
        for ( auto i = 1u; i < inputs.size(); ++i )
          tt &= vs.at( i );
        tt = ~tt;
      }
      else if ( type == "OR" )
      {
        tt = vs.at( 0u );
        for ( auto i = 1u; i < inputs.size(); ++i )
          tt |= vs.at( i );
      }
      else if ( type == "NOR" )
      {
        tt = vs.at( 0u );
        for ( auto i = 1u; i < inputs.size(); ++i )
          tt |= vs.at( i );
        tt = ~tt;
      }
      else
      {
        assert( false && "unsupported gate type" );
      }
      signals[output] = _ntk.create_node( input_signals, tt );
    }
  }

mutable std::map<std::string, signal<Ntk>> signals;

private:
  Ntk& _ntk;
  mutable std::vector<std::string> outputs;
};

}


inline std::pair<std::string, std::map<std::string, std::string>> enumerate_cuts(const std::string &circuit, int cut_size, int cut_limit, int fanout_size) {
    mockturtle::klut_network aig;
    auto bench_reader = mockturtle::public_bench_reader(aig);
    std::istringstream in(circuit);
    auto const result = lorina::read_bench(in, bench_reader);
    auto signals = bench_reader.signals;

    std::map <std::string, std::string> index_to_node;
    for (auto signal: signals)
    {
        index_to_node[std::to_string(signal.second)] = signal.first;
    }

    std::cerr << "bench file is read" << std::endl;
    if (result != lorina::return_code::success)
    {
        std::cerr << "Read benchmark failed" << std::endl;
        return std::make_pair("", index_to_node);
    }
    mockturtle::cut_enumeration_params ps;
    ps.cut_size = cut_size;
    ps.cut_limit = cut_limit;
    ps.fanin_limit = fanout_size;
    std::cerr << "Start enumeration" << std::endl;
    auto const cuts = cut_enumeration(aig, ps);
    std::cerr << "Finish enumeration" << std::endl;

    std::stringstream out;
    aig.foreach_node([&](auto node)
    {
        if (node >= 2)
        {
            out << "Node: " << aig.node_to_index(node) << "\n";
            out << cuts.cuts(aig.node_to_index(node)) << "\n";
        }
    });

    return std::make_pair(out.str(), index_to_node);
}