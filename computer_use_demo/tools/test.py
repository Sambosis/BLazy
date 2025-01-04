# test.py
# imports c:/Downloads/fill_nan_combined_df.csv and adds a unique index to the dataframe
import pandas as pd

def main():
    df = pd.read_csv(r"C:\Users\Machine81\Downloads\fillnan_combined_df.csv")
    df['index'] = 1
    # saves the df to a new csv file
    df.to_csv(r"C:\Users\Machine81\Downloads\fillnan_combined_df_index.csv", index=False)

if __name__ == '__main__':
    main()