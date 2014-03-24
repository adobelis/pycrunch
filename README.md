## pycrunch - A Python library for the CrunchBase API.

pycrunch provides a convenient interface for pulling data from the CrunchBase API. To use:

First, get an API object.
```
>>> from pycrunch.crunchbase import CrunchBase
>>> cb = CrunchBase('myapikeyabc123hov8675309')
```
You can use this object to perform searches:
```
>>> li = cb.search('linkedin')
```
The search function returns an iterator:
```
>>> li1 = li.next()
>>> li1
<Company: LinkedIn>
```
But the search renders only stub objects. To get a full object, use get_full_object():
```
>>> li1 = cb.get_full_object(li1)
```
Once you have a full object you can query it in a natural way:
```
>>> li1.funding_rounds
[<FundingRound: $4700000.0 (USD) Series a: funded 2003-11-01 by [<FinancialOrg: Sequoia Capital>, <Person: Josh Kopelman>]>, <FundingRound: $10000000.0 (USD) Series b: funded 2004-10-01 by [<FinancialOrg: Greylock Partners>]>, <FundingRound: $12800000.0 (USD) Series c: funded 2007-01-29 by [<FinancialOrg: Bessemer Venture Partners>, <FinancialOrg: European Founders Fund>]>, <FundingRound: $53000000.0 (USD) Series d: funded 2008-06-17 by [<FinancialOrg: Bain Capital Ventures>, <FinancialOrg: Sequoia Capital>, <FinancialOrg: Greylock Partners>, <FinancialOrg: Bessemer Venture Partners>]>, <FundingRound: $22700000.0 (USD) Series e: funded 2008-10-22 by [<FinancialOrg: Bessemer Venture Partners>, <FinancialOrg: SAP Ventures>, <FinancialOrg: Goldman Sachs>, <Company: McGraw-Hill Companies>]>, <FundingRound: $81713488.0 (USD) Series post_ipo_equity: funded 2013-05-01 by []>, <FundingRound: $21207933.0 (USD) Series unattributed: funded 2007-03-20 by []>]
```
You can also ask for objects directly:
```
>>> sc = cb.fin_org(name='sequoia capital')
>>> sc
<FinancialOrg: Sequoia Capital>
```
When you do, you get the full object, not a stub.
```
>>> len(sc.investments)
657
```

