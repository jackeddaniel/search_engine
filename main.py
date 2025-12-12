from pathlib import Path
from index_builder import build_index

def main():
    DIR_NAME = "datasets/docs"

    path = Path(DIR_NAME)

    inverted_index = build_index(path)

    print(len(inverted_index))

    count = 0

    for key, val in inverted_index.items():
        if count >= 5:
            break

        print(f"{key} : {val}")
        count += 1


if __name__ == "__main__":
    main()
