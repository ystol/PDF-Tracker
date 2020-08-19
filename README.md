# PDF-Tracker
Tracks and Analyzes electronic markup data on pdfs given (focus on AEC related pdfs such as drawings). The purpose of this project is to give BIM managers and other team members an idea of what the current progress of the drawings is. It is most useful for the BIM manager to be able to quickly identify which drawings are currently outstanding and need to be assigned, as well as other information that can be extracted from the drawing markup data. 

# Getting Started
## Libraries
The libraries that are needed for the script to function as intended are:
- [pdfrw](https://github.com/pmaupin/pdfrw) 
- [pandas](https://pandas.pydata.org/)
- (if using SQL) [my-sql-connector](https://dev.mysql.com/downloads/connector/python/) for python
- All other libraries used will typically come with a default python installation.

## Workflow Recommended
The requirements needed for this to function are the following:
- A single folder with all the drawings for analysis stored inside, using a typical **_[DwgNo.] [DwgDescription] [Revision]_** format. E.g: C-100 PLAN VIEW, C-100 PLAN VIEW (1), or something similar.
- All markups are to be electronically made (Bluebeam, Adobe).
- Both the Engineer team and the BIM team follow the following basic workflow:
  - Drawing plotted for engineers to review.
  - Markups are added to the drawing, and a stamp by the author is placed (Engineer Team. Stamp type does not matter too much, but recommended that this contains the date and the author name).
  - Markups are picked up and worked on as needed, once all markups are complete, a stamp is placed by the author who completed (BIM team).
  - A new drawing is printed and submitted for next revision round.

## Starting/Running
Have all the PDF files for analysis in a single folder, and run '_Run Excel Config Setup.bat_' and then '_Run Excel Full Analysis.bat_'. The script will prompt for a folder, navigate to the pdf folder location and the script will run the analysis. After completion of the script, the **Pdf_Data** excel sheet will populate with extracted data. 
- Adjust the names of the BIM/Engineer team members as needed for the script to be able to flag stamps and data correctly. 

_Running using SQL database_ - Similar to above base setup, except run the .bat file with SQL instead in the same order. The config setup will prompt for the SQL database information (if not already setup) and the project to run analysis on. 

## Visualization Examples
Sample Visualizations can be found **Sample Images**
1. Outstanding Drawings - shows drawings that have an engineer stamp placed but are not yet completed by the BIM team. 
2. Backlog Graph - shows the historical data for how many drawings have been submitted for changes vs. how many have been completed on a given day, as well as how many uncompleted remained at the end of that day.
3. All PDF files checking - similar to #1, but can be filtered and viewed for all drawings in the history. Can be used to identify drawings that were completed incorrectly or to see what drawings were completed and by who.
4. High Edit Drawings - a rough indication showing what drawings are often recieving edit submissions, can help get an idea of which drawings are most often changed to help with prioritization
