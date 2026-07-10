cmake_minimum_required(VERSION 3.10)
project(LivyLogsEngines C)

set(CMAKE_C_STANDARD 99)

# Common flags for Windows applications
if(WIN32)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -mwindows")
    link_libraries(user32)
endif()

# List of all engine names from livylogs_main.py
set(ENGINE_NAMES
    "parser"
)

# Build each engine from parser.c
foreach(ENGINE_NAME ${ENGINE_NAMES})
    add_executable(${ENGINE_NAME} parser.c)
    # Ensure they are output to the root directory where Python expects them
    set_target_properties(${ENGINE_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
endforeach()
