**check for price at NWE lower near or lower avg or lower far on H4 and Daily**

 

* if lower near true then do not check OB and divergence indicators and move to check next symbol

 

* if lower avg  true  then check OB (bullish obs, bullish fvg, breaker support) on H4 and Daily and Weekly, if on more than one, then take status for all to send on the alert message.

   if OB true  then check Divergence (bullish divergence) on H4 and Daily

&nbsp;	if Divergence true then send alert message with NWE status, OB status and divergence status

     	if Divergence false then send alert message with NWE status OB status and divergence false status

   if OB False then don't check divergence indicator. Send alert  message with NWE status and OB false status and divergence status "checking condition not met"

   	



* if lower far true then check OB (bullish obs, bullish fvg, breaker support) on H4 and Daily and Weekly, if on more than one, then take status for all of them to send on the alert message.

&nbsp;	if OB true  then check Divergence (bullish divergence) on H4 and Daily

 		if Divergence true then send alert message with NWE status, OB status and divergence status

	 	if Divergence false then send alert message with NWE status OB status and divergence false status

&nbsp;	if OB False then check Divergence (bullish divergence) on H4 and Daily

   		if Divergence true then send alert message with NWE status, OB false status and divergence status

  	 	if Divergence false then send alert message with NWE status OB false status and divergence false status





**check for price at NWE upper near or upper avg or upper far on H4 and Daily**

 

* if upper near true then do not check OB and divergence indicators and move to check next symbol

 

* if upper avg  true  then check OB (bearish obs, bearish fvg, breaker resistance) on H4 and Daily and Weekly, if on more than one, then take status for all to send on the alert message.

     if OB true  then check Divergence (bearish divergence) on H4 and Daily

&nbsp;	if Divergence true then send alert message with NWE status, OB status and divergence status

     	if Divergence false then send alert message with NWE status OB status and divergence false status

     if OB False then don't check divergence indicator. Send alert  message with NWE status and OB false status and divergence status "checking condition not met"

     	



* if upper far true then check OB (bearish obs, bearish fvg, breaker resistance) on H4 and Daily and Weekly, if on more than one, then take status for all of them to send on the alert message.

 	if OB true  then check Divergence (bearish divergence) on H4 and Daily

   		if Divergence true then send alert message with NWE status, OB status and divergence status

  	 	if Divergence false then send alert message with NWE status OB status and divergence false status

 	if OB False then check Divergence (bearish divergence) on H4 and Daily

     		if Divergence true then send alert message with NWE status, OB false status and divergence status

    	 	if Divergence false then send alert message with NWE status OB false status and divergence false status













