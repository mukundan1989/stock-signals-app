"use client"

import { useState, useEffect } from "react"
import { ChevronDown, Loader2 } from "lucide-react"

interface StockSignal {
  date: string
  comp_symbol: string
  sentiment_score: number
  sentiment: string
  entry_price: number
}

interface PerformanceData {
  symbol: string
  name: string
  lockDate: string
  lockPrice: number
  lockSentiment: string
  currentPrice: number
  change: number
  changePercent: number
  currentSentiment: string
}

// Company name mapping for common stock symbols
const companyNames: Record<string, string> = {
  AAPL: "Apple Inc.",
  MSFT: "Microsoft Corp.",
  GOOGL: "Alphabet Inc.",
  AMZN: "Amazon.com Inc.",
  META: "Meta Platforms Inc.",
  TSLA: "Tesla Inc.",
  NVDA: "NVIDIA Corp.",
  NFLX: "Netflix Inc.",
  JPM: "JPMorgan Chase & Co.",
  V: "Visa Inc.",
  // Add more mappings as needed
}

export default function PerformancePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])
  const [lastUpdated, setLastUpdated] = useState<string>("")

  // Format date to YYYY-MM-DD
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toISOString().split("T")[0]
  }

  // Get company name from symbol
  const getCompanyName = (symbol: string) => {
    return companyNames[symbol] || `${symbol} Inc.`
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch data from all three signal APIs
        const [googleRes, twitterRes, newsRes] = await Promise.all([
          fetch("/api/gtrend-signals"),
          fetch("/api/twitter-signals"),
          fetch("/api/news-signals"),
        ])

        if (!googleRes.ok || !twitterRes.ok || !newsRes.ok) {
          throw new Error("Failed to fetch signal data")
        }

        const [googleData, twitterData, newsData] = await Promise.all([
          googleRes.json(),
          twitterRes.json(),
          newsRes.json(),
        ])

        // Get sets of stock symbols from each source
        const googleStocks = new Set(googleData.map((item: StockSignal) => item.comp_symbol))
        const twitterStocks = new Set(twitterData.map((item: StockSignal) => item.comp_symbol))
        const newsStocks = new Set(newsData.map((item: StockSignal) => item.comp_symbol))

        // Find stocks that appear in all three sources (intersection)
        const commonStocks = [...googleStocks].filter((symbol) => twitterStocks.has(symbol) && newsStocks.has(symbol))

        if (commonStocks.length === 0) {
          setPerformanceData([])
          setLoading(false)
          setError("No stocks found with signals in all three models")
          return
        }

        // Create a map to easily look up signal data by symbol
        const googleMap = new Map(googleData.map((item: StockSignal) => [item.comp_symbol, item]))
        const twitterMap = new Map(twitterData.map((item: StockSignal) => [item.comp_symbol, item]))
        const newsMap = new Map(newsData.map((item: StockSignal) => [item.comp_symbol, item]))

        // Process data for common stocks
        const processedData: PerformanceData[] = []

        for (const symbol of commonStocks) {
          try {
            const googleSignal = googleMap.get(symbol)
            const twitterSignal = twitterMap.get(symbol)
            const newsSignal = newsMap.get(symbol)

            if (!googleSignal || !twitterSignal || !newsSignal) continue

            // Find the most recent signal date among the three sources
            const dates = [new Date(googleSignal.date), new Date(twitterSignal.date), new Date(newsSignal.date)]
            const mostRecentDate = new Date(Math.max(...dates.map((d) => d.getTime())))
            const formattedDate = formatDate(mostRecentDate.toISOString())

            // Determine which signal to use based on the most recent date
            let lockSignal: StockSignal
            if (mostRecentDate.getTime() === dates[0].getTime()) {
              lockSignal = googleSignal
            } else if (mostRecentDate.getTime() === dates[1].getTime()) {
              lockSignal = twitterSignal
            } else {
              lockSignal = newsSignal
            }

            // Get current price using Yahoo Finance
            // For demo purposes, we'll simulate this with a random change
            // In production, replace this with actual Yahoo Finance API call
            const lockPrice = Number.parseFloat(lockSignal.entry_price.toString())
            const randomChange = Math.random() * 20 - 5 // Random change between -5% and +15%
            const changePercent = randomChange
            const change = (lockPrice * changePercent) / 100
            const currentPrice = lockPrice + change

            // Determine current sentiment (for demo, we'll use the most recent sentiment)
            // In production, you might want to calculate this differently
            const currentSentiment = lockSignal.sentiment

            processedData.push({
              symbol,
              name: getCompanyName(symbol),
              lockDate: formattedDate,
              lockPrice,
              lockSentiment: lockSignal.sentiment,
              currentPrice,
              change,
              changePercent,
              currentSentiment,
            })
          } catch (err) {
            console.error(`Error processing stock ${symbol}:`, err)
            // Continue with other stocks even if one fails
          }
        }

        // Sort by symbol
        processedData.sort((a, b) => a.symbol.localeCompare(b.symbol))

        setPerformanceData(processedData)
        setLastUpdated(new Date().toLocaleDateString())
      } catch (err: any) {
        console.error("Error fetching performance data:", err)
        setError(err.message || "Failed to fetch performance data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="bg-white min-h-screen">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="bg-slate-900 text-white p-4 rounded-t-lg">
          <h1 className="text-2xl font-bold">Performance Summary</h1>
        </div>

        {/* Main Content */}
        <div className="bg-white border border-gray-200 rounded-b-lg shadow-sm">
          {/* Table Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">Stocks Performance Table</h2>
                <p className="text-sm text-gray-500">
                  Performance data for stocks with signals in all three models (Google Trends, Twitter, News)
                </p>
              </div>
              <div className="relative">
                <button className="flex items-center justify-between w-full md:w-auto px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none">
                  <span>All Common Stocks</span>
                  <span className="ml-2 text-xs text-gray-500">{performanceData.length} stocks</span>
                  <ChevronDown className="ml-2 h-4 w-4 text-gray-500" />
                </button>
              </div>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex justify-center items-center p-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-600">Loading performance data...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 text-red-600 border border-red-200 rounded-md m-4">{error}</div>
          ) : performanceData.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No stocks found with signals in all three models (Google Trends, Twitter, News)
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr>
                    <th colSpan={2} className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">
                      Stock
                    </th>
                    <th colSpan={2} className="px-6 py-3 bg-blue-100 text-gray-700 border-b border-gray-200">
                      Locked
                    </th>
                    <th className="px-6 py-3 bg-blue-100 text-gray-700 border-b border-gray-200">Sentiment</th>
                    <th colSpan={3} className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">
                      Current
                    </th>
                  </tr>
                  <tr>
                    <th className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">Symbol</th>
                    <th className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">Name</th>
                    <th className="px-6 py-3 bg-blue-100 text-gray-700 border-b border-gray-200">Date</th>
                    <th className="px-6 py-3 bg-blue-100 text-gray-700 border-b border-gray-200">Price</th>
                    <th className="px-6 py-3 bg-blue-100 text-gray-700 border-b border-gray-200">Sentiment</th>
                    <th className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">Price</th>
                    <th className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">Change</th>
                    <th className="px-6 py-3 bg-blue-50 text-gray-700 border-b border-gray-200">Sentiment</th>
                  </tr>
                </thead>
                <tbody>
                  {performanceData.map((stock, index) => (
                    <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-gray-900">{stock.symbol}</td>
                      <td className="px-6 py-4 text-gray-700">{stock.name}</td>
                      <td className="px-6 py-4 text-gray-700 bg-blue-50">{stock.lockDate}</td>
                      <td className="px-6 py-4 text-gray-700 bg-blue-50">${stock.lockPrice.toFixed(2)}</td>
                      <td className="px-6 py-4 bg-blue-50">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-md ${
                            stock.lockSentiment.toLowerCase() === "positive"
                              ? "bg-green-100 text-green-800"
                              : stock.lockSentiment.toLowerCase() === "negative"
                                ? "bg-red-100 text-red-800"
                                : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {stock.lockSentiment}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium text-gray-900">${stock.currentPrice.toFixed(2)}</td>
                      <td className="px-6 py-4 font-medium text-green-600">
                        {stock.change >= 0 ? (
                          <>
                            ↑ +{stock.change.toFixed(2)} (+{stock.changePercent.toFixed(2)}%)
                          </>
                        ) : (
                          <>
                            ↓ {stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                          </>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-md ${
                            stock.currentSentiment.toLowerCase() === "positive"
                              ? "bg-green-100 text-green-800"
                              : stock.currentSentiment.toLowerCase() === "negative"
                                ? "bg-red-100 text-red-800"
                                : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {stock.currentSentiment}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="p-4 text-xs text-gray-500 text-center border-t border-gray-200">
                Stock data as of {lastUpdated}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
