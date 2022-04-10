from os.path import exists
import pandas as pd
from enum import Enum

OUTPUT_HEADER = ["Transaction Type","Transaction ID","Tax lot ID","Asset name","Amount","Date Acquired","Cost basis (USD)","Date of Disposition","Proceeds (USD)","Gains (Losses) (USD)","Holding period (Days)","Data source"]

class DataSource(Enum):
    Coinbase = 1


class TaxGen:
    def __init__(self):
        self.data = None
        self.loaded_file = {}

    def load(self, source: DataSource, path:str):
        if source == DataSource.Coinbase:
            self.load_coinbase(path)

    def load_coinbase(self, path:str):
        file_exists = exists(path)
        if not file_exists:
            print(f"{path} does not exist, try again with different path\n")
            return
        # prevent user from loading same file again
        if path in self.loaded_file:
            print(f"{path} already loaded, try another file\n")
            return
        tmp = pd.read_csv(path, index_col="trade id")
        if self.data is None:
            self.data = tmp
        else:
            self.data = pd.concat([ self.data, tmp ])
        self.loaded_file[path] = len(tmp.index)
        print(f"successfully loaded {len(tmp.index)}, total data after load: {len(self.data.index)}")

    def print_files(self):
        print ("Loaded files:")
        print (self.loaded_file)
        print ("\n")

    def print_stats(self):
        print ("Data stats:")
        print (self.data.groupby(['product','side']).agg({'total': ['count', 'sum']}))
        print ('\n')

    def gen_tax_reports(self):
        opath = ""
        while not exists(opath):
            opath = input( "output file path: " )
        # populate tax_year and txt_date for simplifying filter query
        self.data['txt_date'] = pd.to_datetime(self.data['created at'])
        self.data['tax_year'] = pd.DatetimeIndex(self.data['txt_date']).year
        self.data['remain_size'] = self.data['size']

        tax_years = self.data['tax_year'].unique()
        tax_years.sort()
        for y in tax_years:
            file_name = f"{opath}/coinbase_gainloss_{y}.csv"
            df_sell = self.data[( self.data['tax_year']==y ) & ( self.data['side']=='SELL' ) & ( self.data['remain_size'] > 0 )]
            df_sell = df_sell.sort_values('txt_date')

            df_output = pd.DataFrame()

            for index, row in df_sell.iterrows():
                # find matching buy transactions
                # match the oldest first
                df_buy = self.data[(self.data['txt_date'] < row['txt_date']) & ( self.data['remain_size'] > 0 ) & (self.data['product'] == row['product']) & ((self.data['side'] == 'BUY') | (self.data['side'] == "DEPOSIT"))]
                df_buy = df_buy.sort_values('txt_date', ascending=False)
                if len(df_buy.index) == 0:
                    print("WARNING! No matchable buy rows found, make sure you load all your transactions in")
                    continue
                sell_fee_ratio = row['fee'] / (row['size'] * row['price'])
                for ibuy, rbuy in df_buy.iterrows():
                    buy_fee_ratio = rbuy['fee'] / (rbuy['size'] * rbuy['price'])
                    txt_size = 0
                    if rbuy['remain_size'] >= row['remain_size']:
                        txt_size = row['remain_size']
                        rbuy['remain_size'] -= row['remain_size']
                        row['remain_size'] = 0
                    else:
                        txt_size = row['remain_size'] - rbuy['remain_size']
                        row['remain_size'] -= rbuy['remain_size']
                        rbuy['remain_size'] = 0

                    self.data.loc[index, ( 'remain_size' )] = row['remain_size']
                    self.data.loc[ibuy, ( 'remain_size' )] = rbuy['remain_size']

                    txt_amount = txt_size
                    cost_basis = txt_size * rbuy['price'] * (1.0 + buy_fee_ratio)
                    proceeds = txt_size * row['price'] * (1.0 - sell_fee_ratio)
                    gains = proceeds - cost_basis
                    holdings = row['txt_date'] - rbuy['txt_date']

                    tax_line = {}
                    tax_line['Transaction Type'] = "SELL"
                    tax_line['Transaction ID'] = index
                    tax_line['Tax lot ID'] = y
                    tax_line['Asset name'] = row['product']
                    tax_line['Amount'] = txt_amount
                    tax_line['Date Acquired'] = rbuy['txt_date']
                    tax_line['Cost basis (USD)'] = cost_basis
                    tax_line['Date of Disposition'] = row['txt_date']
                    tax_line['Proceeds (USD)'] = proceeds
                    tax_line['Gains (Losses) (USD)'] = gains
                    tax_line['Holding period (Days)'] = holdings
                    tax_line['Data source'] = 'Coinbase'
                    df_output = pd.concat([ df_output, pd.DataFrame(tax_line, index=[1]) ], ignore_index = True)

                    # if the sell already matched fully, break from this buy loop
                    if (row['remain_size'] == 0):
                        break
            # finish for y write to file
            df_output.to_csv(file_name)
            print(f"df_output size: {len(df_output)}")
        print(f"Finished generated {len(tax_years)} files")
