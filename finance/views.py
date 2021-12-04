from django.shortcuts import render, HttpResponse
import yfinance
import requests_cache
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt  
import requests
# Create your views here.


def homepage(request):
    return render(request, 'finance/index.html')

@csrf_exempt
def ticker_info(request):
    if request.method == 'POST':
        ticker = request.POST['tickers']
        query_string = {
            'symbols': ticker,
            'region': 'US',
            'lang': 'en',
        }
        headers = { 'x-api-key': 'zqKMQGhqkuafWtdhUEKT91oQTvdWmoTLMSy7WDAi'}
        response = requests.request("GET", settings.YAHOO_API + 'qoute', headers=headers, params=query_string)
        print(response.text)
        return HttpResponse(json.loads(response.text))

def create_session():
    session = requests_cache.CachedSession('yfinance.cache')
    session.headers['User-agent'] = 'my-program/1.0'
    session.headers['x-api-key'] = settings.API_KEY
    return session

stock = dict()
dashboard = dict()
@csrf_exempt
def calculate_ticker_data(request):
    tickers = ['NDX','AAPL','MSFT','AMZN','FB','TSLA']
    combined_data = {'column_headers':tickers}
    for ticker in tickers:
        stock[ticker] = get_stock_dataframe(ticker)
        cumulative, annualize = get_performance(ticker)
        dashboard[ticker] = {'cumulative':cumulative,'annualize':annualize}
    return HttpResponse(json.dumps(dashboard))
    
# def prepare_ticker_chart_data(ticker):
#     query_string = {
#         'symbols': ticker,
#         'region': 'US',
#         'lang': 'en',
#     }
#     headers = { 'X-API-KEY': settings.API_KEY }
#     chart_data = requests.request("GET", settings.YAHOO_API + 'charts', headers=headers, params=query_string).text
#     chart_data = json.loads(chart_data)
#     return chart_data

def calculate_monthly_return(df):
    """Calculate the monthly return of the stock"""
    monthly_return = [0]
    monthly_return_perc = [0]
    for index in range(1,len(df.index)):
        month_adj_close = df.iloc[index]['Adj Close']
        previous_adj_close = df.iloc[index-1]['Adj Close']
    
        monthly_return.append(100*(month_adj_close - previous_adj_close)/previous_adj_close)
        monthly_return_perc.append((month_adj_close - previous_adj_close)/previous_adj_close)
    return monthly_return,monthly_return_perc

def get_stock_dataframe(ticker):
    df =  yfinance.download(ticker, start="2015-12-01", end="2020-12-31",interval ="1mo",session=create_session())
    df_adjclose = df.drop(['Open','High','Low','Close','Volume'], axis = 1)
    df_adjclose=df_adjclose.dropna()
    df_adjclose['Monthly Return'],df_adjclose['Monthly Return Perc'] = calculate_monthly_return(df_adjclose)
    return df_adjclose

def calculate_cumulative_return(df,months=3):
    out = 1
    M = len(df.index)
    for index in range(M-months,M,):
        out *= (df.iloc[index]['Monthly Return Perc']+1)
    out = out - 1
    return out, out*100

def calculate_annualize_return(df,months=12):
    out = 1
    M = len(df.index)
    for index in range(M-months,M,):
        out *= (df.iloc[index]['Monthly Return Perc']+1)
    out = (out**(12/months))-1
    return out, out*100

def get_performance(ticker):
    cumulative = {
        'period':['1M','3M','6M','1Y','2Y','3Y','5Y'],
        'stock':[],
        'benchmark':[],
        'active_return':[]
    }
    annualize = {
        'period':['1M','3M','6M','1Y','2Y','3Y','5Y'],
        'stock':[],
        'benchmark':[],
        'active_return':[]
    }
    for month in [1,3,6,12,24,36,60]:
        cumulative['stock'].append(calculate_cumulative_return(stock[ticker],month)[1])
        cumulative['benchmark'].append(calculate_cumulative_return(stock['NDX'],month)[1])
        cumulative['active_return'].append(-cumulative['benchmark'][-1]+cumulative['stock'][-1])
        if month <12:
            annualize['stock'].append(cumulative['stock'][-1])
            annualize['benchmark'].append(cumulative['benchmark'][-1])
            annualize['active_return'].append(cumulative['active_return'][-1])
        else:
            annualize['stock'].append(calculate_annualize_return(stock[ticker],month)[1])
            annualize['benchmark'].append(calculate_annualize_return(stock['NDX'],month)[1])
            annualize['active_return'].append(-annualize['benchmark'][-1]+annualize['stock'][-1])
    
    return cumulative, annualize

def investment(start_date,end_date,investment,stock):
    stock_list = ['AAPL','MSFT','AMZN','FB','TSLA']
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    tickers_length = len(stock_list)
    
    normal = 0
     # Caclulate investment return for equal trading strategy
    for ticker in stock_list:
        df = stock[ticker][start_date:end_date]
        result = 0
        for index in range(len(df.index)):
            result += (df.iloc[index]['Monthly Return Perc']* (investment/tickers_length))+(investment/tickers_length)
        normal += result

    momentum = investment
    length = 0
    returns = []
    
    # Next ticker for first investment
    try:
        for ticker in stock_list:
            returns.append(stock[ticker][stock[ticker].index<start_date].iloc[-1]['Monthly Return Perc'])
        next_ticker = stock_list[returns.index(max(returns))]
    except:
        next_ticker = 'AAPL'
    
    # Filter out stock list within date range
    for ticker in stock_list:
        stock[ticker] = stock[ticker][start_date:end_date]
        length = len(stock[ticker].index)

     
    # Caclulate investment return for momentum trading strategy
    for index in range(length):
        momentum += (stock[next_ticker].iloc[index]['Monthly Return Perc']/100*(momentum) )
        maximum = -float('inf')
        for ticker in stock_list:
            if maximum<=stock[ticker].iloc[index]['Monthly Return Perc']:
                maximum = stock[ticker].iloc[index]['Monthly Return Perc']
                next_ticker = ticker

    return normal, momentum



# def do_investment(start_date,end_date,investment):
#     td = (end_date - start_date).days
#     if td>=365*5:
#         for ticker in dashboard:
#             max_return = max(dashboard[ticker]['annualize'][])