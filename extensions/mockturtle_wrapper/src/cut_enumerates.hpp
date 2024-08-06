#pragma once

#include <map>
#include <string>
#include <filesystem>
#include <iostream>

#include <mockturtle/mockturtle.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/io/write_bench.hpp>

inline std::map<std::string, std::string> enumerate_cuts(const std::string &data_dir) {
    int i = 0;

    std::map <std::string, std::string> res;
    for (const auto &entry: std::filesystem::directory_iterator(data_dir)) {
        mockturtle::klut_network aig;
        std::cerr << entry.path() << "\n";
        auto const result = lorina::read_bench(entry.path(), mockturtle::bench_reader(aig));
        std::cerr << "bench file is read" << std::endl;
        if (result != lorina::return_code::success) {
            std::cerr << "Read benchmark failed" << std::endl;
            return {};
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
        i += 1;
        res[entry.path().filename().string()] = out.str();
    }
    return res;
}