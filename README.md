# Tradingview to Everywhere

## What this does (high level overview)
This opens Tradingview and sets it up. Then python gets a set of upto 5 symbols from a category (the categories are Us Stocks, Indian Stocks, Crypto etc.) It changes the symbol of the chart to the 1st symbol of that set (so that an alert can get created for that symbol). Then Python goes to the screener and fills it up with all those symbols in the set. The maximum number of symbols it can fill into the screener are 5. After that, an alert gets set for the screener. This process continues until Python covers all the symbols of every category.

After alerts have been created for all the symbols, Python checks the "Alert log" for messages from the alerts it created. Every message comes from a specific alert. So, every message will have the entries which came from the screener which that specific alert was set to. There can be a single entry or multiple entries in a message.

Python then goes through each message which came. It reads each entry in that message. Python then goes to that entry's symbol and timeframe. Then it fills up the entry time, entry price, TP and SL of that entry in an indicator. That other indicator then draws the entry based on the info it has been filled up with. The drawing will look like this: ![Alt text](media/entry-drawing.png) 

Then, Python takes a snapshot of that and send it to Discord, Poolsifi and a database.

This whole process is repeated for all the messages until there are no more left. Once there are no more messages left, Python waits for them to come.

## Things to do for programmers:

