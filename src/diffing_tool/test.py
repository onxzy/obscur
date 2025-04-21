from diffing_tool import diffing_texts, read_file

if __name__ == '__main__':
    path1 = "../ranion_parsed.txt"
    path2 = "../ranion2_parsed.txt"

    text1 = read_file(path1)
    text2 = read_file(path2)

    modification_detected, summary  =  diffing_texts(text1, text2)

    print(f"Modification detected: {modification_detected}")
    print(summary)
