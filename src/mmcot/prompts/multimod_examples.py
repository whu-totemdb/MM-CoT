"""Retained research prompt content; no provider or service dependencies."""

EXAMPLES = {
    "SubSet": """In PostgreSQL, academic graph data is stored through relational tables, which can be divided into node tables and edge tables. The specific information is as follows:\n
    Node tables:\n
        1. Paper: PaperID (primary key), PaperTitle, Year, ReferenceCount, CitationCount, Publisher, Date, DocType, OriginalVenue\n
        2. Author: AuthorID (primary key), Author_Name, H-index, Productivity, Average_C10\n
        3. Affiliation: AffiliationID (primary key), Affiliation_Name, GridID, Latitude, Longitude, H-index, Productivity, Average_C10, Official_Page, ISO3166Code\n
    Edge tables:\n
        1. PaperAuthor: PaperID, AuthorID\n
        2. PaperAffiliation: PaperID, AffiliationID  \n
        3. AuthorAffiliation: AuthorID, AffiliationID\n
        4. Reference: Citing_PaperID, Cited_PaperID\n
        5. Collab: AuthorID1, AuthorID2, Count, PaperList\n

    Question: How many publications did Korea University of Science and Technology have in 2017?\n
    Thought 1: The question is asking about the number of publications that an affiliation wrote in 2017. We need to find the node corresponding to Korea University of Science and Technology in the graph.\n
    Action 1: RetrieveNode[Korea University of Science and Technology]\n
    Observation 1: The node for this affiliation is Affiliation/57882.\n
    Thought 2: The question is asking for the number of publications in 2017, so we need to check the Affiliation node's paper neighbors from the graph.\n
    Action 2: NeighbourCheck[Affiliation, 57882, Paper]\n
    Observation 2: Found 1234 matching tuples. Example: [{'paperid': 2055378633, 'doi': '10.1016/J.CUB.2006.09.005', 'doctype': 'Journal', 'papertitle': 'The Fat Cadherin Acts through the Hippo Tumor-Suppressor Pathway to Regulate Tissue Size', 'booktitle': None, 'year': 2006, 'date': datetime.date(2006, 11, 7), 'publisher': 'Cell Press', 'journalid': 128425624.0, 'conferenceseriesid': None, 'volume': Decimal('16.0'), 'issue': '21.0', 'firstpage': '2090', 'lastpage': '2100', 'referencecount': 52, 'citationcount': 276, 'originalvenue': 'Current Biology', 'familyid': None, 'retractiontype': None}]\n
    Thought 3: Then we need to filter the papers published in 2017.\n
    Action 3: FilterByRange[result_2, Year, 2017, 2017]\n
    Observation 3: Found 135 documents within the range. Example: [{'PaperID': 157773358, 'DocType': 'Conference', 'PaperTitle': 'A Study on the Application of Big Data in Smart City Construction', 'Year': 2017, 'Date': '2017-01-01', 'Publisher': 'Science Press', 'ReferenceCount': 0, 'CitationCount': 1, 'OriginalVenue': 'Modern Preventive Medicine'}]\n
    Thought 4: Now I have the papers published in 2017. Let me show the count and some details.\n
    Action 4: ShowDetail[result_3, PaperTitle, Year]\n
    Observation 4: Detailed results for result_3 (attributes: PaperTitle, Year): [{"PaperTitle": "A Study on the Application of Big Data in Smart City Construction", "Year": 2017}, {"PaperTitle": "Machine Learning Applications in Healthcare", "Year": 2017}, {"PaperTitle": "Blockchain Technology for Data Security", "Year": 2017}] and 132 more records.\n
    Thought 5: Korea University of Science and Technology had 135 publications in 2017.\n
    Action 5: Finish[135]\n
    Final answer:135.

    Question: How many papers did Wei Fang write and which one is most highly cited?\n
    Thought 1: The question is asking for the number of papers which Wei Fang wrote and the most highly cited one. We need to locate the node corresponding to Wei Fang.\n
    Action 1: RetrieveNode[Wei Fang]\n
    Observation 1: The node for this author is Author/12345.\n
    Thought 2: We have gotten the author node, then we need to get his papers.\n
    Action 2: NeighbourCheck[Author, 12345, Paper]\n
    Observation 2: Found 6 matching documents. Example: [{'PaperID': 333922273, 'DocType': 'Journal', 'PaperTitle': 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH', 'Year': 2009, 'Date': '2009-01-01', 'Publisher': 'Magazine House of Modern Preventive Medicine', 'ReferenceCount': 0, 'CitationCount': 1, 'OriginalVenue': 'Modern Preventive Medicine'}]\n
    Thought 3: Now we know Wei Fang has written 6 papers, and now we need to find the most highly cited one.\n
    Action 3: Sort[result_2, CitationCount, 1]\n
    Observation 3: Sort and extract 1 documents. Example: [{'PaperID': 333922273, 'DocType': 'Journal', 'PaperTitle': 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH', 'Year': 2009, 'Date': '2009-01-01', 'Publisher': 'Magazine House of Modern Preventive Medicine', 'ReferenceCount': 0, 'CitationCount': 1, 'OriginalVenue': 'Modern Preventive Medicine'}]\n
    Thought 4: Let me show the details of the most cited paper by Wei Fang.\n
    Action 4: ShowDetail[result_3, PaperTitle, CitationCount, Year]\n
    Observation 4: Detailed results for result_3 (attributes: PaperTitle, CitationCount, Year): [{"PaperTitle": "IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH", "CitationCount": 25, "Year": 2009}].\n
    Thought 5: Wei Fang has written 6 papers, and the most highly cited one is 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH' with 25 citations.\n
    Action 5: Finish[Wei Fang has written 6 papers, the most highly cited one is 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH' with 25 citations.]\n
    Final answer: Wei Fang has written 6 papers, the most highly cited one is 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH' with 25 citations.\n

    Question: Who is the closest collaborator of the author "Greg Daville"?\n
    Thought 1: The question asks for the closest collaborator of Greg Daville. First, I need to find the node for Greg Daville in the graph.\n
    Action 1: RetrieveNode[Greg Daville]\n
    Observation 1: The node for this author is Author/127997586.\n
    Thought 2: To find collaborators, I need to find all collaboration edges starting from this author node.\n
    Action 2: EdgeCheck_LinkNode[Author, 127997586, Collab]\n
    Observation 2: Found 5 edges linking to node. Example: [{"AuthorID1": 127997586, "AuthorID2": 23456789, "Count": 12, "PaperList": ["1001", "1002"]}, {"AuthorID1": 127997586, "AuthorID2": 34567890, "Count": 3, "PaperList": ["1003"]}]\n
    Thought 3: The closest collaborator is the one with the highest collaboration count. I need to sort these edges by the Count field and get the top one.\n
    Action 3: Sort[result_2, Count, 1]\n
    Observation 3: Sort and extract 1 documents. Example: [{"AuthorID1": 127997586, "AuthorID2": 23456789, "Count": 12, "PaperList": ["1001", "1002"]}]\n
    Thought 4: Now I need to get the detailed information of the collaborator node.\n
    Action 4: NodeDetail[Author, 23456789]\n
    Observation 4: The details of Author/23456789 are: {"AuthorID": 23456789, "Author_Name": "Alice Smith", "H-index": 20, "Productivity": 50, "Average_C10": 15.2}\n
    Thought 5: Let me show the detailed information about the closest collaborator including the collaboration count.\n
    Action 5: ShowDetail[result_4, Author_Name, H-index]\n
    Observation 5: Detailed results for result_4 (attributes: Author_Name, H-index): [{"Author_Name": "Alice Smith", "H-index": 20}].\n
    Thought 6: The closest collaborator of Greg Daville is Alice Smith with 12 collaborations.\n
    Action 6: Finish[Alice Smith]\n
    Final answer: Alice Smith\n

    Question: What are the top three institutions in terms of the number of publications in 2023?\n
    Thought 1: The question is asking for the top 3 institutions in terms of the number of publications in 2023. We need to filter out the papers published in 2023 from the Paper table.\n
    Action 1: FilterByRange[Paper, Year, 2023, 2023]\n
    Observation 1: Found 1234 documents within the range. Example: [{"PaperID": 2023001, "PaperTitle": "Advances in Large Language Models", "Year": 2023, "CitationCount": 120, "OriginalVenue": "Artificial Intelligence"}]\n
    Thought 2: Find the corresponding documents in the PaperAffiliation table based on the papers from result_1.\n
    Action 2: Join[result_1, PaperAffiliation, PaperID, PaperID]\n
    Observation 2: Found 2345 matching tuples in target collection. Example: [{"PaperID": 2023001, "AffiliationID": 1001, "AuthorID": 5001}]\n
    Thought 3: Group and count the affiliations by AffiliationID.\n
    Action 3: GroupAggregate[result_2, AffiliationID, count]\n
    Observation 3: Grouped into 456 groups, example: [{"AffiliationID": 1001, "count": 10}]\n
    Thought 4: Sort the results and truncate to the top three documents.\n
    Action 4: Sort[result_3, count, 3]\n
    Observation 4: Sort and extract 3 documents. Example: [{"AffiliationID": 1001, "count": 10}]\n
    Thought 5: Use the AffiliationID to find the detailed information of the institutions in the Affiliation table.\n
    Action 5: Join[result_4, Affiliation, AffiliationID, AffiliationID]\n
    Observation 5: Found 3 matching tuples in target collection. Example: [{"AffiliationID": 1001, "Affiliation_Name": "Stanford University", "H-index": 210, "Productivity": 4500, "Average_C10": 85}]\n
    Thought 6: Show the detailed information of the top institutions including their names and publication counts.\n
    Action 6: ShowDetail[result_5, Affiliation_Name, count]\n
    Observation 6: Detailed results for result_5 (attributes: Affiliation_Name, count): [{"Affiliation_Name": "Stanford University", "count": 10}, {"Affiliation_Name": "Massachusetts Institute of Technology", "count": 9}, {"Affiliation_Name": "University of California, Berkeley", "count": 8}].\n
    Thought 7: Now I have the complete information to answer the question about the top 3 institutions with the most publications in 2023.\n
    Action 7: Finish[1. Stanford University; 2. Massachusetts Institute of Technology; 3. University of California, Berkeley]\n
    Final answer: 1. Stanford University; 2. Massachusetts Institute of Technology; 3. University of California, Berkeley\n
    """
}
