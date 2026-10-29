cmake_minimum_required(VERSION 3.20)
project(ur_devnode_benchmark LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(ur_devnode_tour_test
  "${CMAKE_CURRENT_LIST_DIR}/../../tests/native/modern_tour_continue_test.cpp")
target_include_directories(ur_devnode_tour_test PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../../native/product")
# Debug builds preserve real assertions in the existing game test.
