# Python-Stock-Options-Loader
Load table option_table1 with stock options using finance.yahoo.com as a data source.
The code requires an SQL table called option_table1 to be created. Option data is loaded in that table.

Note: this is a part of a complete investment decision process where 

STEP 1 - stocks are being selected with their probabilities for a share price increase

STEP 2 - next, the options of this stock selection are downloaded; this 'Python Stock Options Loader' code snippet

STEP 3 - apply predicted end prices at strike date for each option

STEP 4 - a final query can select the most profitable option


So this code snippet performs STEP 2 - download the option prices

The option prices are also plotted for each expiration date and option type. Example of a plot:
![image](https://user-images.githubusercontent.com/78446548/106661868-04871100-65a2-11eb-83fc-ecf50ae69e50.png)

The table is loaded with the option pricing and quotation details:

![image](https://user-images.githubusercontent.com/78446548/106670773-c394f980-65ad-11eb-870d-531f74ef1ad3.png)
