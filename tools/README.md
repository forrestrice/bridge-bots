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
|       Name       | Value                                                                                        |
|:----------------:|:---------------------------------------------------------------------------------------------|
|     board_id     | Board name                                                                                   |
|       file       | Originating file                                                                             |
|    deal_hash     | A unique identifier of the deal, dealer, and vulnerability                                   |
|      north       | Player name                                                                                  |
|      south       | Player name                                                                                  |
|       east       | Player name                                                                                  |
|       west       | Player name                                                                                  |
|      dealer      | Direction                                                                                    |
|    vulnerable    | Which seats are vulnerable. One of: `all`, `none`, `1-3` (declarer r/w), `2-4`(declarer w/r) |
|     bidding      | The bids, alerts, and announcements from the auction                                         |
|      opener      | Which seat opened (1-indexed)                                                                |
|     opening      | Bid                                                                                          |
|    opener_hcp    | Opener's Goren high card points                                                              |
|   opener_shape   | Opener's shape in descending suit order                                                      |
|  overcall_type   | One of `None`, `Direct`, `Sandwich`, or `Balance`                                            |
|     overcall     | Bid                                                                                          |
|  overcaller_hcp  | Overcallers's Goren high card points                                                         |
| overcaller_shape | Overcaller's shape in descending suit order                                                  |
|    contested     | True if the team that didn't open made any action other than PASS                            |
|   competitive    | True if each team made at least two bids                                                     |
|     declarer     | Direction                                                                                    |
|     contract     | Final Contract                                                                               |
|       lead       | Card led                                                                                     |
|      result      | Outcome (e.g. 2H-2)                                                                          |
|      tricks      | Number of tricks taken by declarer                                                           |
|     score_ns     | Score for north-south                                                                        |
|     score_ew     | Score for east-west                                                                          |
|  score_declarer  | Score for declarer's team                                                                    |
|  score_defender  | Score for defenders' team                                                                    |
|       link       | BBO link to board_record                                                                     |
|  declarer_shape  | Declarer's shape in suit order                                                               |
|   dummy_shape    | Dummy's shape in suit order                                                                  |
|    lho_shape     | Declarer's left-hand opponent shape in suit order                                            |
|    rho_shape     | Declarer's right-hand opponent shape suit order                                              |
|   declarer_hcp   | Declarer's high card points                                                                  |
|    dummy_hcp     | Dummy's high card points                                                                     |
|     lho_hcp      | Declarer's left-hand opponent high card points                                               |
|     rho_hcp      | Declarer's right-hand opponent high card points                                              |
|    trump_fit     | Number of trumps held by declarer + dummy                                                    |
|    trump_hcp     | Number of high card points held by declarer + dummy in the trump suit                        |

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

## Compare Contracts Report
This is an analysis tool for investigating how one set of contracts compares with another in your bridge data. It will allow you to find deals where a contract from set A was played at one table, but a contract from set B was played at another. This could be used to evaluate choice of games/slams or competitive decisions like 5H over 4S.

### Running
The compare contracts report function can be run as a python script:
`python compare_contracts_csv_report.py`

Or as a module:
`python -m bridgebots_tools.compare_contracts_csv_report`

### Arguments
List all arguments by running with `--help`
```shell script
python -m bridgebots_tools.compare_contracts_csv_report --help
Usage: python -m bridgebots_tools.compare_contracts_csv_report 
           [OPTIONS] CONTRACT_SETS... INPUT_PATH [OUTPUT_PATH]

Options:
  --input_format [lin|pbn]
  --deal_comparison_type [same_deal|any]
  --direction_comparison_type [same_direction|opposite_direction|any]
  --lax_doubles / --strict_doubles
  -v, --verbose
  --info
  -q, --quiet
  --help                          Show this message and exit.
```
- `input_format`: the type of files to read (pbn or lin). Default is lin.

- `deal_comparison_type`: In `same_deal` mode the tool will only find comparisons where a contract from each contract set occurred in the same deal. In `any` mode all boards that played in a contract in either contract set will be included.

- `direction_comparison_type`: In `same_direction` mode, the contracts must have been played by the same pair (e.g. North-South). This is useful for comparing a choice of contracts (e.g. 3NT vs 4H,4S). In `opposite_direction` mode, the contracts must have been played by opposite pairs. This is useful for comparing decisions to compete (e.g. 5H vs 4S). In `any` mode, all boards will be included.

- Doubles Flags:
  - `lax_doubles`: Consider undoubled, doubled, and redoubled contracts to be equivalent.
  - `strict_doubles`: Consider undoubled, doubled, and redoubled contracts to be distinct. Doubled and redoubled contracts can be included in contract sets (e.g. 2CX).

- Log Level Flags :
    - `verbose/-v` output debugging information such as files processed and number of deals found. 
    - `--info` Default log level. Includes warnings about malformed records.
    - `--quiet/-q` No output

- `CONTRACT_SETS`: Two arguments. Each is a comma separated list of contracts to be compared with the other set. For example, you might provide the arguments `3NT` and `4H,4S` to compare major suit games with 3NT.    

- `INPUT_PATH` path to a bridge file or directory containing bridge files. If a directory is used, it will be searched recursively.

- `OUTPUT_PATH` path to output csv file. If not supplied, the csv will be written to stdout.
### Output Fields
See the csv_report output fields above. 

### Examples

```shell script
python -m bridgebots_tools.compare_contracts_csv_report 3NT 4H,4S .
```
```text
board_id,file,deal_hash,north,south,east,west,dealer,vulnerable,bidding,opener,opening,opener_hcp,opener_shape,overcall_type,overcall,overcaller_hcp,overcaller_shape,contested,competitive,declarer,contract,lead,result,tricks,score_ns,score_ew,score_declarer,score_defender,link,declarer_shape,dummy_shape,lho_shape,rho_shape,declarer_hcp,dummy_hcp,lho_hcp,rho_hcp,trump_fit,trump_hcp
c7,sfa1.lin,-6400932905757015746,Balicki,Zmudzinski,Helness,Helgemo,south,all,PASS|PASS|PASS|1NT|PASS|2H!|PASS|2S|PASS|3NT|PASS|PASS|PASS,4,1NT,17,3343,,,,,False,False,east,3NT,D4,3NT+1,10,-630,630,630,-630,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CZmudzinski%2CHelgemo%2CBalicki%2CHelness%7Cst%7C%7Cmd%7C1S54HK32DQ954CA974%2CSAKJ72HJ75D832CT8%2CST83HT964DA6CJ532%2CSQ96HAQ8DKJT7CKQ6%7Cah%7CBoard+7%7Csv%7Cb%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7C1N%7Cmb%7Cp%7Cmb%7C2H%21%7Cmb%7Cp%7Cmb%7C2S%7Cmb%7Cp%7Cmb%7C3N%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CD4%7Cpc%7CD2%7Cpc%7CDA%7Cpc%7CD7%7Cpg%7C%7Cpc%7CCJ%7Cpc%7CCK%7Cpc%7CCA%7Cpc%7CC8%7Cpg%7C%7Cpc%7CC4%7Cpc%7CCT%7Cpc%7CC2%7Cpc%7CC6%7Cpg%7C%7Cpc%7CD3%7Cpc%7CD6%7Cpc%7CDJ%7Cpc%7CDQ%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C,3343,5332,2344,3424,17,9,9,5,,
o7,sfa1.lin,-6400932905757015746,Fantoni,Nunes,Lynch,Passell,south,all,PASS|PASS|PASS|1NT|PASS|2C|PASS|2D|PASS|2S|PASS|4S|PASS|PASS|PASS,4,1NT,17,3343,,,,,False,False,west,4S,DA,4S-1,9,100,-100,-100,100,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CNunes%2CPassell%2CFantoni%2CLynch%7Cst%7C%7Cmd%7C1S54HK32DQ954CA974%2CSAKJ72HJ75D832CT8%2CST83HT964DA6CJ532%2CSQ96HAQ8DKJT7CKQ6%7Cah%7CBoard+7%7Csv%7Cb%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7C1N%7Cmb%7Cp%7Cmb%7C2C%7Cmb%7Cp%7Cmb%7C2D%7Cmb%7Cp%7Cmb%7C2S%7Cmb%7Cp%7Cmb%7C4S%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CDA%7Cpc%7CD7%7Cpc%7CD4%7Cpc%7CD8%7Cpg%7C%7Cpc%7CD6%7Cpc%7CDK%7Cpc%7CD5%7Cpc%7CD3%7Cpg%7C%7Cpc%7CSQ%7Cpc%7CS5%7Cpc%7CS2%7Cpc%7CS3%7Cpg%7C%7Cpc%7CS6%7Cpc%7CS4%7Cpc%7CSK%7Cpc%7CS8%7Cpg%7C%7Cpc%7CSA%7Cpc%7CST%7Cpc%7CS9%7Cpc%7CC4%7Cpg%7C%7Cpc%7CC8%7Cpc%7CC2%7Cpc%7CCK%7Cpc%7CCA%7Cpg%7C%7Cpc%7CDQ%7Cpc%7CD2%7Cpc%7CH6%7Cpc%7CDT%7Cpg%7C%7Cpc%7CD9%7Cpc%7CH5%7Cpc%7CH4%7Cpc%7CDJ%7Cpg%7C%7Cpc%7CCQ%7Cpc%7CC7%7Cpc%7CCT%7Cpc%7CC3%7Cpg%7C%7Cpc%7CC6%7Cpc%7CC9%7Cpc%7CS7%7Cpc%7CC5%7Cpg%7C%7Cmc%7C9%7Cpg%7C%7C,5332,3343,3424,2344,9,17,5,9,8,10
```


## Practice Deals Builder
This tool is designed for building sets of practice deals for use on BBO. A user can supply a specific lin file and board number and the tool will create (or append) a LIN and CSV containing the deal and all the information available from the csv_report tool.

### Running
The practice deals tool can be run as a python script:
`python practice_deals.py`

Or as a module:
`python -m bridgebots_tools.practice_deals`

### Arguments
List all arguments by running with `--help`
```shell script
python -m bridgebots_tools.practice_deals --help
Usage: python -m bridgebots_tools.practice_deals [OPTIONS] INPUT_DIR FILE_NAME
                                                 BOARD [OUTPUT_LIN]
                                                 [OUTPUT_CSV]

Options:
  --input_format [lin|pbn]
  -v, --verbose
  --info
  -q, --quiet
  --help                    Show this message and exit.
```
- `input_format`: the type of files to read (pbn or lin). Default is lin.

- Log Level Flags :
    - `verbose/-v` Output debugging information.
    - `--info` Default log level. Includes warnings about malformed records.
    - `--quiet/-q` No output
    
- `INPUT_DIR` path to a directory containing bridge files. Will be searched recursively for `FILE_NAME`

- `FILE_NAME` Name of the target file to extract a board from.

- `BOARD` The board number to extract.

- `OUTPUT_LIN` path to output LIN file to create or append. If not supplied, the LIN will be written to stdout.

- `OUTPUT_CSV` path to output CSV file to create or append. If not supplied, the CSV will be written to stdout.

### Examples
Extract board 46 from file `usbf_sf_14502.lin` located in the current working directory.
```shell script
python -m bridgebots_tools.practice_deals . usbf_sf_14502.lin 46
```
```text
qx|o46|st||md|4SJ5H9DAT862CQ8752,SKQT94HAK73DQ4C93,S872HQT5DJ97CAT64,SA63HJ8642DK53CKJ|ah|Board 46|sv|o|mb|1H|mb|p|mb|3C!|an|jacoby 2N|mb|p|mb|4H|mb|p|mb|p|mb|p|pg||pc|C2|pc|C3|pc|CA|pc|CJ|pg||pc|D7|pc|D5|pc|DA|pc|D4|pg||pc|D6|pc|DQ|pc|D9|pc|D3|pg||pc|C9|pc|C4|pc|CK|pc|C5|pg||pc|H2|pc|H9|pc|HA|pc|H5|pg||mc|10|pg||
o_board_id,o_file,o_deal_hash,o_north,o_south,o_east,o_west,o_dealer,o_vulnerable,o_bidding,o_opener,o_opening,o_opener_hcp,o_opener_shape,o_overcall_type,o_overcall,o_overcaller_hcp,o_overcaller_shape,o_contested,o_competitive,o_declarer,o_contract,o_lead,o_result,o_tricks,o_score_ns,o_score_ew,o_score_declarer,o_score_defender,o_link,o_declarer_shape,o_dummy_shape,o_lho_shape,o_rho_shape,o_declarer_hcp,o_dummy_hcp,o_lho_hcp,o_rho_hcp,o_trump_fit,o_trump_hcp,c_board_id,c_file,c_deal_hash,c_north,c_south,c_east,c_west,c_dealer,c_vulnerable,c_bidding,c_opener,c_opening,c_opener_hcp,c_opener_shape,c_overcall_type,c_overcall,c_overcaller_hcp,c_overcaller_shape,c_contested,c_competitive,c_declarer,c_contract,c_lead,c_result,c_tricks,c_score_ns,c_score_ew,c_score_declarer,c_score_defender,c_link,c_declarer_shape,c_dummy_shape,c_lho_shape,c_rho_shape,c_declarer_hcp,c_dummy_hcp,c_lho_hcp,c_rho_hcp,c_trump_fit,c_trump_hcp
o46,usbf_sf_14502.lin,-5685382758932396718,Rodwell,Meckstroth,Weinstein,Levin,east,none,1H|PASS|3C!(jacoby 2N)|PASS|4H|PASS|PASS|PASS,1,1H,12,3532,,,,,False,False,east,4H,C2,4H=,10,-420,420,420,-420,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CMeckstroth%2CLevin%2CRodwell%2CWeinstein%7Cst%7C%7Cmd%7C4SJ5H9DAT862CQ8752%2CSKQT94HAK73DQ4C93%2CS872HQT5DJ97CAT64%2CSA63HJ8642DK53CKJ%7Cah%7CBoard+46%7Csv%7Co%7Cmb%7C1H%7Cmb%7Cp%7Cmb%7C3C%21%7Can%7Cjacoby+2N%7Cmb%7Cp%7Cmb%7C4H%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CC2%7Cpc%7CC3%7Cpc%7CCA%7Cpc%7CCJ%7Cpg%7C%7Cpc%7CD7%7Cpc%7CD5%7Cpc%7CDA%7Cpc%7CD4%7Cpg%7C%7Cpc%7CD6%7Cpc%7CDQ%7Cpc%7CD9%7Cpc%7CD3%7Cpg%7C%7Cpc%7CC9%7Cpc%7CC4%7Cpc%7CCK%7Cpc%7CC5%7Cpg%7C%7Cpc%7CH2%7Cpc%7CH9%7Cpc%7CHA%7Cpc%7CH5%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C,3532,5422,2155,3334,12,14,7,7,9,8,c46,usbf_sf_14502.lin,-5685382758932396718,Martel,Stansby,Mahmood,Hamman,east,none,1H|PASS|2S!|PASS|2NT!|PASS|3H|PASS|4H!(no slam interest)|PASS|PASS|PASS,1,1H,12,3532,,,,,False,False,east,4H,C5,4H=,10,-420,420,420,-420,https://www.bridgebase.com/tools/handviewer.html?lin=pn%7CStansby%2CHamman%2CMartel%2CMahmood%7Cst%7C%7Cmd%7C4SJ5H9DAT862CQ8752%2CSKQT94HAK73DQ4C93%2CS872HQT5DJ97CAT64%2CSA63HJ8642DK53CKJ%7Cah%7CBoard+46%7Csv%7Co%7Cmb%7C1H%7Cmb%7Cp%7Cmb%7C2S%21%7Cmb%7Cp%7Cmb%7C2N%21%7Cmb%7Cp%7Cmb%7C3H%7Cmb%7Cp%7Cmb%7C4H%21%7Can%7Cno+slam+interest%7Cmb%7Cp%7Cmb%7Cp%7Cmb%7Cp%7Cpg%7C%7Cpc%7CC5%7Cpc%7CC3%7Cpc%7CCA%7Cpc%7CCJ%7Cpg%7C%7Cpc%7CC4%7Cpc%7CCK%7Cpc%7CC2%7Cpc%7CC9%7Cpg%7C%7Cpc%7CH2%7Cpc%7CH9%7Cpc%7CHA%7Cpc%7CHT%7Cpg%7C%7Cpc%7CHK%7Cpc%7CH5%7Cpc%7CH4%7Cpc%7CC7%7Cpg%7C%7Cmc%7C10%7Cpg%7C%7C,3532,5422,2155,3334,12,14,7,7,9,8
```