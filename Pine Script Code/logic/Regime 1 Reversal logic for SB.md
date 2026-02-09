
Note: Here are the possible fields and values in the JSON alert message (the format of the JSOn payload can change but the info i.e. fields must be preserved)
{
	OB & FVG: {
		{
			zonetype: FVG or OB,
			type: bullish | bearish | breaker support/breaker resistance,
			zoneTimestamp: [timestmap of when the OB or FVG started],
			overlapTimestamp: [timestamp of when price overlapped  the zone],
			timeframe: H1 or H4 or Daily
		},
		
		*add another object if an FVG/OB was detected on another timeframe
	},

	NWE: {
		{
			zone: the NWE band in which price overlapped,
			type: bullish | bearish,
			overlapTimestamp: [timestamp of when price overlapped  the zone],
			timeframe: H1 or H4
		},
		
		*add another object if this indicator's condition was true on the other timeframe
	},

	Kernel AO DIV: {
		{
			divType: Logic 2,
			type: bullish | bearish,
			Timestamp: [timestamp of div's 2nd high/low],
			timeframe: H1 or H4
		},

		*add another object if this indicator's condition was true on the other timeframe
	}
}

# Bullish logic (check if any one of the 3 is true)

1. check if price on shift 0 is in the NWE lower avg or lower far zones on both the H1 or H4 timeframes. This condition has to be true on at least 1 timeframe but both timeframes must be checked.
	
2. check if price on shift 0 overlaps with any OB/FVG (bullish ob, bullish fvg, breaker support) on the H1, H4 and Daily timeframes. This condition has to be true on at least 1 timeframe but all 3 timeframes must be checked.

3. check if a bullish regular divergence's 2nd low (logic 2) on H1 and H4 timeframes is on shift 0. This condition has to be true on at least 1 timeframe but both timeframes must be checked. 


# Bearish logic (check if any one of the 3 is true)

1. check if price on shift 0 is in the NWE upper avg or upper far zones on both the H1 or H4 timeframes. This condition has to be true on at least 1 timeframe but both timeframes must be checked.
	
2. check if price on shift 0 overlaps with any OB/FVG (bearish ob, bearish fvg, breaker resistance) on the H1, H4 and Daily timeframes. This condition has to be true on at least 1 timeframe but all 3 timeframes must be checked.

3. check if a bearish regular divergence's 2nd high (logic 2) on H1 and H4 timeframes is on shift 0. This condition has to be true on at least 1 timeframe but both timeframes must be checked. 

Note (for both the bullish and bearish logic)  that if any condition has occurred on more than 1 timeframe, the condition on each timeframe will be considered separate