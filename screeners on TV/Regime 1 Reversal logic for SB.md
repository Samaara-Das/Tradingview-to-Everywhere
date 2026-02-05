Note: An alert message is sent by the screener which is formatted in JSON. When status is mentioned below, it is the value of a field. the fields in the JSON are the indicators  - NWE, OB & FVG, Divergences. The status is false if the indicator's condition was not fulfilled. If it was fulfilled, the status will be an object containing info about the signal. 

Note: Here are the possible fields and values in the JSON alert message
{
	OB & FVG: {
		{
			zonetype: FVG or OB,
			type: bullish | bearish | breaker support/breaker resistance,
			zoneTimestamp: [timestmap of when the OB or FVG started],
			overlapTimestamp: [timestamp of when price overlapped  the zone],
			timeframe: H4 or Daily or Weekly
		},
		
		*add another object if an FVG/OB was detected on another timeframe
	},

	NWE: {
		{
			zone: the NWE band in which price overlapped,
			type: bullish | bearish,
			overlapTimestamp: [timestamp of when price overlapped  the zone],
			timeframe: H4 or Daily
		},
		
		*add another object if this indicator's condition was true on the other timeframe
	},

	Kernel AO DIV: {
		{
			divType: Logic 2,
			type: bullish | bearish,
			Timestamp: [timestamp of div's 2nd high/low],
			timeframe: H4 or Daily
		},

		*add another object if this indicator's condition was true on the other timeframe
	}
}

# Bullish logic (check these conditions in order and only move on to the next condition if the current one is fulfilled)

1. check if price on shift 0 is in the NWE lower avg or lower far zones on both the H4 or Daily timeframes. This condition has to be true on at least 1 timeframe to proceed to the next condition but both timeframes must be checked.
	
	2. check if price on shift 0 overlaps with any OB/FVG (bullish ob, bullish fvg, breaker support) on the H4, Daily and Weekly timeframes. This condition has to be true on at least 1 timeframe to proceed to the next condition but all 3 timeframes must be checked.

		3. check if a bullish regular divergence's 2nd low (logic 2) on H4 and Daily timeframes is on shift 0. This condition has to be true on at least 1 timeframe to proceed to the next condition but both timeframes must be checked. 

Send an alert message if at least 1 condition in this particular order is true. 


# Bearish logic (check these conditions in order and only move on to the next condition if the current one is fulfilled)

1. check if price on shift 0 is in the NWE upper avg or upper far zones on both the H4 or Daily timeframes. This condition has to be true on at least 1 timeframe to proceed to the next condition but both timeframes must be checked.
	
	2. check if price on shift 0 overlaps with any OB/FVG (bearish ob, bearish fvg, breaker resistance) on the H4, Daily and Weekly timeframes. This condition has to be true on at least 1 timeframe to proceed to the next condition but all 3 timeframes must be checked.

		3. check if a bearish regular divergence's 2nd high (logic 2) on H4 and Daily timeframes is on shift 0. This condition has to be true on at least 1 timeframe to proceed to the next condition but both timeframes must be checked. 

Send an alert message if at least 1 condition in this particular order is true. 
