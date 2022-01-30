# Tools
Bridgebots Tools is a suite of tools for finding, processing, and analyzing bridge data. It utilizes the [Bridgebots Core package](https://github.com/forrestrice/bridge-bots/tree/master/bridgebots) to parse and represent data.

## Setup
### Package Install
Install the Bridgebots Tools package with `pip install bridgebots_tools`.

### Building From Source
Install the package with `poetry install`

## CSV Report
The `csv_report` script extracts bridge data from a directory or file. It currently supports PBN and LIN formats.

### Running
The report function can be run as a python script:
`python csv_report.py`

Or as a module:
`python -m bridgebots_tools.csv_report`

### Arguments
List all arguments by running with `--help`
```shell script
python -m bridgebots_tools.csv_report --help
Usage: python -m bridgebots_tools.csv_report [OPTIONS] INPUT_PATH
                                             [OUTPUT_PATH]

Options:
  --input_format [lin|pbn]
  --output_format [team|individual]
  -v, --verbose
  --info
  -q, --quiet
  --help                          Show this message and exit.
```

- `input_format`: the type of files to read (pbn or lin). Default is lin.

- `output_format`: In `individual` mode each play of a board will have its own row in the output csv. In `team` mode a single row will be created for each pair of boards in the match, allowing for easy comparision. Columns will be prefixed with `o_` or `c_` to represent play in the open/closed rooms.

- Log Level Flags :
    - `verbose/-v` output debugging information such as files processed and number of deals found. 
    - `--info` Default log level. Includes warnings about malformed records.
    - `--quiet/-q` No output
    
- `INPUT_PATH` path to a bridge file or directory containing bridge files. If a directory is used, it will be searched recursively.

- `OUTPUT_PATH` path to output csv file. If not supplied, the csv will be written to stdout.

### Output Fields
| Name      | Value |
| :---:        |    :----  |
|board_id| Board name|
|file| Originating file|
|north| Player name|
|south|Player name|
|east|Player name|
|west|Player name|
|dealer|Direction|
|vulnerable|Which seats are vulnerable. One of: `all`, `none`, `1-3` (declarer r/w), `2-4`(declarer w/r)|
|bidding|The bids, alerts, and announcements from the auction|
|opener|Which seat opened (1-indexed)|
|opening|Bid|
|opener_hcp|Opener's Goren high card points|
|opener_shape|Opener's shape in descending suit order|
|overcall_type|One of `None`, `Direct`, `Sandwich`, or `Balance`|
|overcall|Bid|
|overcaller_hcp|Overcallers's Goren high card points|
|overcaller_shape|Overcaller's shape in descending suit order|
|contested|True if the team that didn't open made any action other than PASS|
|declarer|Direction|
|contract|Final Contract|
|lead|Card led|
|result|Outcome (e.g. 2H-2)|
|tricks|Number of tricks taken by declarer|
|score_ns|Score for north-south|
|score_ew|Score for east-west|
|link|BBO link to board_record|


### Examples
Run the report on a single LIN file and output in team format:
```shell script
$ python -m bridgebots_tools.csv_report tools_example/r16b8.lin tools_example/r16b8.csv
$ head -n 3 tools_example/r16b8.csv
```
```text
o_board_id,o_file,o_north,o_south,o_east,o_west,o_dealer,o_vulnerable,o_bidding,o_opener,o_opening,o_opener_hcp,o_opener_shape,o_overcall_type,o_overcall,o_overcaller_hcp,o_overcaller_shape,o_contested,o_declarer,o_contract,o_lead,o_result,o_tricks,o_score,o_link,c_board_id,c_file,c_north,c_south,c_east,c_west,c_dealer,c_vulnerable,c_bidding,c_opener,c_opening,c_opener_hcp,c_opener_shape,c_overcall_type,c_overcall,c_overcaller_hcp,c_overcaller_shape,c_contested,c_declarer,c_contract,c_lead,c_result,c_tricks,c_score,c_link
o46,r16b8.lin,Bathurst,Moss,Feldman,Watson,east,none,2H|PASS|4H|PASS|PASS|PASS,1,2H,6,2551,,,,,False,east,4H,DA,4H-1,9,-50,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CMoss%2CWatson%2CBathurst%2CFeldman%7Cst%7C%7Cmd%7C4S8632H8DA6CK96432%2CSAK4HKJ62DQJ532C7%2CSQT95HA93D7CAQJT8%2CSJ7HQT754DKT984C5%7Cah%7CBoard+46%7Csv%7Co%7Cmb%7C2H%7Cmb%7Cp%7Cmb%7C4H%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CDA%7Cpc%7CD2%7Cpc%7CD7%7Cpc%7CD9%7Cpg%7C%7Cpc%7CD6%7Cpc%7CD3%7Cpc%7CH3%7Cpc%7CDK%7Cpg%7C%7Cpc%7CCA%7Cpc%7CC5%7Cpc%7CC2%7Cpc%7CC7%7Cpg%7C%7Cmc%7C9%7Cpg%7C%7C,c46,r16b8.lin,Hung,J. Stansby,Hampson,Greco,east,none,PASS|PASS|1D!(2+)|2C|2H|X!|4H|4S|PASS|PASS|X|PASS|PASS|PASS,3,1D,14,3451,direct,2C,13,4315,True,north,4SX,C5,4SX=,10,590,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CJ.+Stansby%2CGreco%2CHung%2CHampson%7Cst%7C%7Cmd%7C4S8632H8DA6CK96432%2CSAK4HKJ62DQJ532C7%2CSQT95HA93D7CAQJT8%2CSJ7HQT754DKT984C5%7Cah%7CBoard+46%7Csv%7Co%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7C1D%21%7Can%7C2%2B%7Cmb%7C2C%7Cmb%7C2H%7Cmb%7CX%21%7Cmb%7C4H%7Cmb%7C4S%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7CX%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CC5%7Cpc%7CCK%7Cpc%7CC7%7Cpc%7CCQ%7Cpg%7C%7Cpc%7CS2%7Cpc%7CS4%7Cpc%7CST%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CH5%7Cpc%7CH8%7Cpc%7CHK%7Cpc%7CHA%7Cpg%7C%7Cpc%7CSQ%7Cpc%7CS7%7Cpc%7CS3%7Cpc%7CSK%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C
o47,r16b8.lin,Bathurst,Moss,Feldman,Watson,south,1-3,PASS|PASS|3C|PASS|PASS|PASS,3,3C,10,0157,,,,,False,north,3C,SQ,3C+1,10,130,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CMoss%2CWatson%2CBathurst%2CFeldman%7Cst%7C%7Cmd%7C1SAT43HKJ976D985CK%2CSK965HT832DQ4CQ54%2CSHQDA7632CAT98762%2CSQJ872HA54DKJTCJ3%7Cah%7CBoard+47%7Csv%7Cn%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7C3C%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CSQ%7Cpc%7CSA%7Cpc%7CS5%7Cpc%7CHQ%7Cpg%7C%7Cpc%7CCK%7Cpc%7CC4%7Cpc%7CC2%7Cpc%7CC3%7Cpg%7C%7Cpc%7CD9%7Cpc%7CDQ%7Cpc%7CDA%7Cpc%7CDK%7Cpg%7C%7Cpc%7CCA%7Cpc%7CCJ%7Cpc%7CH7%7Cpc%7CC5%7Cpg%7C%7Cpc%7CD6%7Cpc%7CDT%7Cpc%7CD5%7Cpc%7CD4%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C,c47,r16b8.lin,Hung,J. Stansby,Hampson,Greco,south,1-3,2D!(Flannery)|PASS|3C|PASS|PASS|PASS,1,2D,11,4531,,,,,False,north,3C,CJ,3C+1,10,130,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CJ.+Stansby%2CGreco%2CHung%2CHampson%7Cst%7C%7Cmd%7C1SAT43HKJ976D985CK%2CSK965HT832DQ4CQ54%2CSHQDA7632CAT98762%2CSQJ872HA54DKJTCJ3%7Cah%7CBoard+47%7Csv%7Cn%7Cmb%7C2D%21%7Can%7CFlannery%7Cmb%7Cp%7Cmb%7C3C%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CCJ%7Cpc%7CCK%7Cpc%7CC5%7Cpc%7CC2%7Cpg%7C%7Cpc%7CSA%7Cpc%7CS5%7Cpc%7CHQ%7Cpc%7CS2%7Cpg%7C%7Cpc%7CS3%7Cpc%7CS9%7Cpc%7CC6%7Cpc%7CS7%7Cpg%7C%7Cpc%7CCA%7Cpc%7CC3%7Cpc%7CH6%7Cpc%7CC4%7Cpg%7C%7Cpc%7CDA%7Cpc%7CDJ%7Cpc%7CD5%7Cpc%7CD4%7Cpg%7C%7Cpc%7CD2%7Cpc%7CDT%7Cpc%7CD8%7Cpc%7CDQ%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C
```

Run the report in quiet mode on a directory of pbn files and output in individual format:
```shell script
$ python -m bridgebots_tools.csv_report -q --input_format=pbn --output_format=individual tools_example/ tools_example/usbc.csv
$ wc -l tools_example/usbc.csv 
    4031 tools_example/usbc.csv
$ head -n 3 tools_example/usbc.csv
board_id,file,north,south,east,west,dealer,vulnerable,bidding,opener,opening,opener_hcp,opener_shape,overcall_type,overcall,overcaller_hcp,overcaller_shape,contested,declarer,contract,lead,result,tricks,score,link
,usbc_2011.pbn,Moss,Gitelman,Bathurst,Zagorin,north,none,1D|PASS|1NT|PASS|3NT|PASS|PASS|PASS,1,1D,16,2263,,,,,False,south,3NT,S5,3NT-4,5,-200,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CGitelman%2CZagorin%2CMoss%2CBathurst%7Cst%7C%7Cmd%7C3SQ6HQT7DJ98CJ8742%2CSK9853HA84D43CAT3%2CSJ7HK6DAKQ765CK96%2CSAT42HJ9532DT2CQ5%7Csv%7Co%7Cmb%7C1D%7Cmb%7Cp%7Cmb%7C1N%7Cmb%7Cp%7Cmb%7C3N%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CS5%7Cpc%7CS7%7Cpc%7CSA%7Cpc%7CS6%7Cpg%7C%7Cpc%7CS2%7Cpc%7CSQ%7Cpc%7CSK%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CS9%7Cpc%7CC6%7Cpc%7CST%7Cpc%7CC7%7Cpg%7C%7Cpc%7CS4%7Cpc%7CC4%7Cpc%7CS8%7Cpc%7CD5%7Cpg%7C%7Cpc%7CS3%7Cpc%7CH6%7Cpc%7CH2%7Cpc%7CH7%7Cpg%7C%7Cpc%7CC3%7Cpc%7CC9%7Cpc%7CCQ%7Cpc%7CC2%7Cpg%7C%7Cpc%7CC5%7Cpc%7CC8%7Cpc%7CCA%7Cpc%7CCK%7Cpg%7C%7Cpc%7CHA%7Cpc%7CHK%7Cpc%7CH3%7Cpc%7CHT%7Cpg%7C%7Cmc%7C5%7Cpg%7C%7C
,usbc_2011.pbn,Grue,Lall,Greco,Hampson,north,none,1C|PASS|1D|1S|X|3H|PASS|3S|PASS|PASS|PASS,1,1C,16,2263,sandwich,1S,11,5323,True,west,3S,DK,3S-1,8,-50,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CLall%2CHampson%2CGrue%2CGreco%7Cst%7C%7Cmd%7C3SQ6HQT7DJ98CJ8742%2CSK9853HA84D43CAT3%2CSJ7HK6DAKQ765CK96%2CSAT42HJ9532DT2CQ5%7Csv%7Co%7Cmb%7C1C%7Cmb%7Cp%7Cmb%7C1D%7Cmb%7C1S%7Cmb%7CX%7Cmb%7C3H%7Cmb%7Cp%7Cmb%7C3S%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CDK%7Cpc%7CD2%7Cpc%7CD8%7Cpc%7CD3%7Cpg%7C%7Cpc%7CDA%7Cpc%7CDT%7Cpc%7CD9%7Cpc%7CD4%7Cpg%7C%7Cpc%7CHK%7Cpc%7CH2%7Cpc%7CH7%7Cpc%7CHA%7Cpg%7C%7Cpc%7CS3%7Cpc%7CS7%7Cpc%7CSA%7Cpc%7CS6%7Cpg%7C%7Cpc%7CS2%7Cpc%7CSQ%7Cpc%7CSK%7Cpc%7CSJ%7Cpg%7C%7Cpc%7CH4%7Cpc%7CH6%7Cpc%7CHJ%7Cpc%7CHQ%7Cpg%7C%7Cpc%7CC2%7Cpc%7CCA%7Cpc%7CC6%7Cpc%7CC5%7Cpg%7C%7Cmc%7C8%7Cpg%7C%7C

```