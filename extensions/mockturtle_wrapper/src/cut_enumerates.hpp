#pragma once

#include <map>
#include <string>
#include <filesystem>
#include <iostream>

#include <mockturtle/mockturtle.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/io/write_bench.hpp>

inline std::pair<std::string, std::map<std::string, std::string>> enumerate_cuts(const std::string &circuit_path) {
    mockturtle::klut_network aig;
    mockturtle::bench_reader bench_reader = mockturtle::bench_reader(aig);
    std::cerr << circuit_path << "\n";
    auto const result = lorina::read_bench(circuit_path, bench_reader);
    auto signals = bench_reader.signals;

    std::map <std::string, std::string> index_to_node;
    for (auto signal: signals) {
        index_to_node[std::to_string(signal.second)] = signal.first;
    }

    std::cerr << "bench file is read" << std::endl;
    if (result != lorina::return_code::success) {
        std::cerr << "Read benchmark failed" << std::endl;
        return std::make_pair("", index_to_node);
    }
    mockturtle::cut_enumeration_params ps;
    ps.cut_size = 5;
    ps.cut_limit = 25;
    ps.fanin_limit = 10000;
    std::cerr << "Start enumeration" << std::endl;
    auto const cuts = cut_enumeration(aig, ps);
    std::cerr << "Finish enumeration" << std::endl;

    std::stringstream out;
    aig.foreach_node([&](auto node) {
        if (node >= 2) {
            out << "Node: " << aig.node_to_index(node) << "\n";
            out << cuts.cuts(aig.node_to_index(node)) << "\n";
        }
    });

    return std::make_pair(out.str(), index_to_node);
}