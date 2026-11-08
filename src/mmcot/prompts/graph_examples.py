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

    Question: How many papers did Wei Fang write?\n
    Thought 1: The question is asking for the number of papers which Wei Fang wrote. I need to locate the node corresponding to Wei Fang first.\n
    Action 1: RetrieveNode[Wei Fang]\n
    Observation 1: The node for this author is Author/12345.\n
    Thought 2: Now I have the author node, I need to get his papers by checking the Paper neighbors of this author.\n
    Action 2: NeighbourCheck[Author, 12345, Paper]\n
    Observation 2: Found 6 matching tuples. Examples: [{'paperid': 333922273, 'doctype': 'Journal', 'papertitle': 'IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH', 'year': 2009, 'date': '2009-01-01', 'publisher': 'Magazine House of Modern Preventive Medicine', 'referencecount': 0, 'citationcount': 1, 'originalvenue': 'Modern Preventive Medicine'}].\n
    Thought 3: I found that Wei Fang has written 6 papers. This answers the question directly.\n
    Action 3: Finish[6]\n
    Final answer: 6.

    Question: Who is the closest collaborator of the author "Greg Daville"?\n
    Thought 1: The question asks for the closest collaborator of Greg Daville. First, I need to find the node for Greg Daville in the graph.\n
    Action 1: RetrieveNode[Greg Daville]\n
    Observation 1: The node for this author is Author/127997586.\n
    Thought 2: To find collaborators, I need to find all collaboration edges starting from this author node.\n
    Action 2: EdgeCheck_LinkNode[Author, 127997586, Collab]\n
    Observation 2: Found 5 edges linking to node. Examples: [{"author1_id": 127997586, "author2_id": 23456789, "count": 12, "paperlist": ["1001", "1002"]}].\n
    Thought 3: Now I need to check the collaboration count for each author in the edges.
    Action 3: ShowDetail[result_2, author1_id, author2_id, count]
    Observation 3: Detailed results for result_2(attributes: author1_id, author2_id, count): [{"author1_id": 127997586, "author2_id": 23456789, "count": 12}, {"author1_id": 127997586, "author2_id": 34567890, "count": 3}, {"author1_id": 127997586, "author2_id": 45678901, "count": 7}, {"author1_id": 127997586, "author2_id": 56789012, "count": 2}, {"author1_id": 127997586, "author2_id": 67890123, "count": 5}].
    Thought 4: I found that author 23456789 has the highest count of 12. Let me get the details of this author.\n
    Action 4: NodeDetail[Author, 23456789]\n
    Observation 4: The details of Author/23456789 are: {"authorid": 23456789, "author_name": "Alice Smith", "h-index": 20, "productivity": 50, "average_c10": 15.2}.\n
    Thought 5: The closest collaborator of Greg Daville is Alice Smith with 12 collaborations.\n
    Action 5: Finish[Alice Smith]\n
    Final answer: Alice Smith\n

    Question: How many collaborations does author "Alice Johnson" have with "Bob Chen"?\n
    Thought 1: I need to find both authors first, then check the collaboration edge between them.\n
    Action 1: RetrieveNode[Alice Johnson]\n
    Observation 1: The node for this author is Author/78901.\n
    Thought 2: Now I need to find Bob Chen.\n
    Action 2: RetrieveNode[Bob Chen]\n
    Observation 2: The node for this author is Author/78902.\n
    Thought 3: Now I can check the collaboration edge between these two authors.\n
    Action 3: EdgeCheck_BetweenNodes[Author, 78901, Author, 78902]\n
    Observation 3: Found collaboration edge with 8 papers co-authored.\n
    Thought 4: Alice Johnson and Bob Chen have collaborated on 8 papers.\n
    Action 4: Finish[8]\n
    Final answer: 8\n

    Question: Who is the author of the paper "IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH"?\n
    Thought 1: I need to find the paper node first.\n
    Action 1: RetrieveNode[IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH]\n
    Observation 1: The node for this paper is Paper/1001.\n
    Thought 2: Now I need to find the authors of this paper.\n
    Action 2: NeighbourCheck[Paper, 1001, PaperAuthor]\n
    Observation 2: Found 2 matching tuples. Examples: [{'authorid': 12345, 'author_name': 'Wei Fang'}, {'authorid': 67890, 'author_name': 'Greg Daville'}].\n
    Thought 3: I need to check the author names in the result.\n
    Action 3: ShowDetail[result_2, authorid, author_name]\n
    Observation 3: Detailed results for result_2(attributes: authorid, author_name): [{"authorid": 12345, "author_name": "Wei Fang"}, {"authorid": 67890, "author_name": "Greg Daville"}].\n
    Thought 4: The authors of the paper "IMPLICATION OF RESPONDENT-DRIVEN SAMPLING IN EPIDEMIOLOGICAL RESEARCH" are Wei Fang and Greg Daville.\n
    Action 4: Finish[Wei Fang, Greg Daville]\n
    Final answer: Wei Fang, Greg Daville\n
    """
}
