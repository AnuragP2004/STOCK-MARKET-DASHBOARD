#include <iostream>
#include <vector>
#include <numeric>
#include <cmath>
#include <string>

using namespace std;
double calculateSMA(const vector<double> &prices, int period)
{
    if (prices.size() < period)
        return 0.0;
    double sum = accumulate(prices.end() - period, prices.end(), 0.0);
    return sum / period;
}

double calculateEMA(const vector<double> &prices, int period)
{
    if (prices.size() < period)
        return 0.0;
    double multiplier = 2.0 / (period + 1);
    double ema = calculateSMA(vector<double>(prices.begin(), prices.begin() + period), period);
    for (size_t i = period; i < prices.size(); ++i)
    {
        ema = (prices[i] - ema) * multiplier + ema;
    }
    return ema;
}

double calculateRSI(const vector<double> &prices, int period)
{
    if (prices.size() <= period)
        return 50.0;
    double gain = 0.0, loss = 0.0;
    for (size_t i = prices.size() - period; i < prices.size(); ++i)
    {
        double change = prices[i] - prices[i - 1];
        if (change > 0)
            gain += change;
        else
            loss -= change;
    }
    gain /= period;
    loss /= period;
    if (loss == 0)
        return 100.0;
    double rs = gain / loss;
    return 100.0 - (100.0 / (1.0 + rs));
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        cerr << "Usage: ./analysis <price1> <price2> ..." << endl;
        return 1;
    }

    vector<double> prices;
    for (int i = 1; i < argc; ++i)
    {
        prices.push_back(stod(argv[i]));
    }

    if (prices.size() < 26)
    {
        cout << "{\"error\": \"Not enough data\"}" << endl;
        return 1;
    }

    double sma14 = calculateSMA(prices, 14);
    double ema14 = calculateEMA(prices, 14);
    double rsi14 = calculateRSI(prices, 14);

    // MACD = EMA(12) - EMA(26)
    double ema12 = calculateEMA(prices, 12);
    double ema26 = calculateEMA(prices, 26);
    double macd = ema12 - ema26;

    // Volatility (Standard Deviation over 14 days)
    double mean = sma14;
    double variance = 0.0;
    for (size_t i = prices.size() - 14; i < prices.size(); ++i)
    {
        variance += pow(prices[i] - mean, 2);
    }
    double volatility = sqrt(variance / 14);

    int trend = (prices.back() > sma14) ? 1 : ((prices.back() < sma14) ? -1 : 0);

    // Print output as JSON
    cout << "{"
         << "\"sma\": " << sma14 << ", "
         << "\"ema\": " << ema14 << ", "
         << "\"rsi\": " << rsi14 << ", "
         << "\"macd\": " << macd << ", "
         << "\"volatility\": " << volatility << ", "
         << "\"trend\": " << trend
         << "}" << endl;

    return 0;
}