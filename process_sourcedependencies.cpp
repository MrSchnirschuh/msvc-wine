/*
 * Copyright (c) 2023 Mircea Roata
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

 #define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#include <stdio.h>

#include <iostream>
#include <fstream>
#include <string>
#include <regex>
    
LPSTR (*CDECL wine_get_unix_file_name_ptr)(LPCWSTR) = NULL;

std::string convertPath(std::string ntpath)
{
    std::string tail; // the end of the path which does not exist. will start with "/"
    std::string result;

    while (true)
    {
        // Convert std::string (UTF-8 or ANSI) to std::wstring (UTF-16)
        std::wstring wntpath(ntpath.begin(), ntpath.end());
        char *unix_name = wine_get_unix_file_name_ptr(wntpath.c_str());
        if (unix_name)
        {
            result = unix_name;
            if (tail.size() > 0)
                result += tail;
            HeapFree(GetProcessHeap(), 0, unix_name);
            break;
        }

        // Handle more than just last component not existing

        std::string::size_type tail_pos = ntpath.find_last_of("/\\");
        if (tail_pos == std::string::npos)
            break; // Windows paths must have at least one separator (z:/)

        std::string::size_type invalid_char_pos = ntpath.find_first_of("*?<>|\"", tail_pos + 1);
        if (invalid_char_pos != std::string::npos)
            break; // Contains invalid ntfs characters, so can never be a valid windows path
        
        tail = "/" + ntpath.substr(tail_pos + 1) + tail;
        ntpath.resize(tail_pos);
    }

    return result;
}

std::regex json_path_regex("\"z:\\\\[^\"]*\"");

int __cdecl wmain(int argc, WCHAR *argv[])
{
    if (argc <= 1) return 0;
    wine_get_unix_file_name_ptr = (LPSTR (CDECL *)(LPCWSTR))GetProcAddress(GetModuleHandleA("KERNEL32"), "wine_get_unix_file_name");
    if (wine_get_unix_file_name_ptr == NULL) {
        std::cerr << "cannot get the address of 'wine_get_unix_file_name'" << std::endl;
        return 3;
    }

    std::wstring filepath = argv[1];

    std::ifstream input_file(filepath);

    if (!input_file.is_open()) {
        std::cerr << "Failed to open input file." << std::endl;
        return 1;
    }

    std::string file_contents((std::istreambuf_iterator<char>(input_file)),
                              std::istreambuf_iterator<char>());
    input_file.close();

    std::string output;
    std::sregex_iterator iter(file_contents.begin(), file_contents.end(), json_path_regex);
    std::sregex_iterator end;
    size_t last_pos = 0;

    while (iter != end) {
        std::smatch match = *iter;
        output.append(file_contents, last_pos, match.position() - last_pos);

        std::string matched_path = match.str().substr(1, match.str().size() - 2); // remove quotes
        std::string converted_path = convertPath(matched_path);
        output += "\"" + converted_path + "\"";

        last_pos = match.position() + match.length();
        ++iter;
    }
    output.append(file_contents, last_pos, std::string::npos);

    std::ofstream output_file(filepath, std::ios::trunc);
    if (!output_file.is_open()) {
        std::cerr << "Failed to open output file for writing." << std::endl;
        return 2;
    }
    output_file << output;
    output_file.close();

    return 0;
}
