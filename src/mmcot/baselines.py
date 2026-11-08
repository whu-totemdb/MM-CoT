"""Retrieval baselines with the supplied keyword and answer prompts."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class BaseLLM:
    def __init__(self, model, domain):
        self.model, self.domain = model, domain

    def query(self, question):
        prompt = f"请回答以下问题。请提供准确、简洁的答案。\n\n在{self.domain}领域中，问题：{question}\n\n请直接回答问题，不需要额外的解释或格式化。"
        return {"query_answer": self.model.complete(prompt), "status": "success", "query_process": ""}


class TextRAG:
    def __init__(self, model, graph, retriever, top_k=1):
        self.model, self.graph_funcs, self.retriever, self.top_k = model, graph, retriever, top_k

    def _call_llm(self, prompt):
        return self.model.complete(prompt)

    def query(self, question):
        keywords = self.extract_keywords(question)
        nodes = [{"id": node_id, "type": kind, "details": self.graph_funcs.check_nodes(kind, node_id)}
                 for node_id, kind in self.retriever.retrieve_node(keywords, self.top_k)]
        context = self.format_context(nodes, keywords)
        return {"query_answer": self.generate_answer(question, context), "status": "success",
                "query_process": context, "keywords": keywords}


    def extract_keywords(self, question: str) -> str:
        """
        Extract keywords from the question using LLM API
        
        Args:
            question: The input question
            
        Returns:
            String containing extracted keywords for retrieval
        """
        keyword_extraction_prompt = f"""You are a keyword extraction expert for academic research. Please analyze the following question and extract the most important keywords that would be useful for retrieving relevant academic papers and research information.
    
        Please focus on extracting the following types of keywords:
        1. **Author Names**: Including first names, last names, or full names (e.g., Zhang San, Smith, John Smith)
        2. **Paper Titles**: Complete or partial paper titles (e.g., "Stress reactions at slaughter", "Machine Learning in Medicine")
        3. **Institution Names**: Universities, research institutes, company names (e.g., Tsinghua University, MIT, Google)
    
        Question: "{question}"
    
        Please extract and return only the most relevant keywords as a single line of text, separated by spaces. Focus on the most important terms that would help find the specific information being asked about.
    
        Keywords:"""
        
        try:
            keywords = self._call_llm(keyword_extraction_prompt)
            
            # Clean up the keywords - remove any extra formatting
            if keywords.startswith("Keywords:") or keywords.startswith("关键词："):
                keywords = keywords.split(":")[-1].split("：")[-1].strip()
            
            # Limit keywords to avoid too long queries
            keyword_list = keywords.split()[:15]  # Limit to 15 keywords
            final_keywords = " ".join(keyword_list)
            
            logger.info(f"Extracted keywords: {final_keywords}")
            return final_keywords
            
        except Exception as e:
            logger.error(f"Error in keyword extraction: {e}")
            # Fallback: use original question
            return question

    def format_context(self, nodes: List[Dict], keywords: str) -> str:
        """
        Format the retrieved nodes into context
        
        Args:
            nodes: List of retrieved nodes
            keywords: Extracted keywords
            
        Returns:
            Formatted context string
        """
        if not nodes:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        
        # Add keywords information
        context_parts.append(f"Search Keywords: {keywords}")
        context_parts.append("")
        
        # Add retrieved information
        context_parts.append("Retrieved Information:")
        
        for i, node in enumerate(nodes, 1):
            context_parts.append(f"Source {i} ({node['type']}):")
            
            details = node['details']
            if isinstance(details, dict):
                for key, value in details.items():
                    if value is not None and str(value).strip():
                        context_parts.append(f"  {key}: {value}")
            else:
                context_parts.append(f"  Content: {details}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)

    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using LLM with question and context
        
        Args:
            question: Original question
            context: Formatted context from retrieved nodes
            
        Returns:
            Generated answer
        """
        prompt = f"""You are an expert academic research assistant. Please provide a concise, direct answer to the following question based on the retrieved information.
    
        Question: {question}
    
        Retrieved Information:
        {context}
    
        Answer Format Guidelines:
        - For questions asking about NUMBERS/QUANTITIES (e.g., "How many papers cite...", "What is the citation count..."): 
          → Respond with ONLY the specific number (e.g., "78")
          
        - For questions asking about AUTHORS (e.g., "Who is the author...", "Who wrote...", "Who are the authors..."):
          → Respond with ONLY the author name(s) (e.g., "John Smith" or "John Smith, Jane Doe")
          
        - For questions asking about PAPER TITLES (e.g., "What is the title...", "Which paper..."):
          → Respond with ONLY the exact paper title (e.g., "Clinical Development of Leukocyte Cyclooxygenase 2 Activity")
          
        - For questions asking about INSTITUTIONS/AFFILIATIONS:
          → Respond with ONLY the institution name(s)
          
        - For questions asking about PUBLICATION DETAILS (year, journal, etc.):
          → Respond with ONLY the requested detail (e.g., "2001" for year, "Nature" for journal)
          
        - For other types of questions:
          → Provide a brief, direct answer focusing on the key information requested
    
        Important Rules:
        1. Be extremely concise - avoid explanations, background information, or elaboration
        2. Extract the exact information requested from the retrieved data
        3. If the specific information is not available, respond with "Information not available"
        4. Do not include phrases like "Based on the retrieved information" or "According to the data"
        5. Just provide the direct answer
    
        Answer:"""
    
        try:
            answer = self._call_llm(prompt)
            return answer.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise

class GraphRAG(TextRAG):
    def query(self, question):
        keywords = self.extract_keywords(question)
        ego_graphs = []
        for node_id, kind in self.retriever.retrieve_node(keywords, self.top_k):
            ego = {"central_node": {"id": node_id, "type": kind,
                                    "details": self.graph_funcs.check_nodes(kind, node_id)},
                   "neighbors": {}, "edges": {}}
            for edge in self.graph_funcs.edge_types:
                edges, ids, target = self.graph_funcs.get_edges_from_node(kind, node_id, edge)
                ego["edges"][edge] = edges
                if ids:
                    ego["neighbors"][f"{target}_via_{edge}"] = self.graph_funcs.check_nodes_batch(target, ids)
            ego_graphs.append(ego)
        context = self.format_ego_graph_context(question, keywords, ego_graphs)
        return {"query_answer": self.generate_answer(question, context), "status": "success",
                "query_process": context, "keywords": keywords}


    def format_ego_graph_context(self, question: str, keywords: List[str], ego_graphs: List[Dict]) -> str:
        """
        Format ego-graphs into context string for LLM with enhanced edge information
        
        Args:
            question: Original question
            keywords: Extracted keywords
            ego_graphs: List of ego-graph dictionaries with detailed edge information
            
        Returns:
            Formatted context string
        """
        context_parts = []
        context_parts.append("Question: " + question)
        context_parts.append(f"Search Keywords: {keywords}")
        context_parts.append("")
        
        # Add ego-graph information
        context_parts.append("Retrieved Graph Context:")
        context_parts.append("")
        
        for i, ego_graph in enumerate(ego_graphs, 1):
            central_node = ego_graph['central_node']
            context_parts.append(f"=== Central Node {i} ({central_node['type']}) ===")
            
            # Add central node details
            if central_node['details']:
                for key, value in central_node['details'].items():
                    if value is not None and str(value).strip():
                        context_parts.append(f"  {key}: {value}")
            context_parts.append("")
            
            # Add neighbor information organized by edge type
            neighbors = ego_graph['neighbors']
            edges = ego_graph.get('edges', {})
            
            if neighbors:
                context_parts.append("Connected Nodes:")
                
                for neighbor_key, neighbor_list in neighbors.items():
                    if neighbor_list:
                        # Extract edge type from neighbor key (e.g., "Author_via_PaperAuthor" -> "PaperAuthor")
                        edge_type = neighbor_key.split('_via_')[-1] if '_via_' in neighbor_key else 'Unknown'
                        
                        context_parts.append(f"  {neighbor_key} ({len(neighbor_list)} nodes):")
                        
                        # Limit the number of neighbors shown
                        max_neighbors = 5
                        for j, neighbor in enumerate(neighbor_list[:max_neighbors]):
                            context_parts.append(f"    - Node {j+1}:")
                            for key, value in neighbor.items():
                                if value is not None and str(value).strip() and key not in ['id']:
                                    # Truncate long values
                                    str_value = str(value)
                                    if len(str_value) > 100:
                                        str_value = str_value[:100] + "..."
                                    context_parts.append(f"      {key}: {str_value}")
                            
                            # Add edge-specific information for Reference and Collab
                            if edge_type in ['Reference', 'Collab'] and edge_type in edges:
                                neighbor_id = neighbor.get(f"{neighbor_key.split('_')[0].lower()}id")
                                if neighbor_id:
                                    relevant_edges = [e for e in edges[edge_type] 
                                                    if str(neighbor_id) in [str(v) for v in e.values()]]
                                    
                                    if relevant_edges:
                                        context_parts.append(f"      Relationship Details:")
                                        for edge in relevant_edges[:2]:  # Limit to 2 edges per neighbor
                                            if edge_type == 'Reference':
                                                # Add citation direction information
                                                direction = edge.get('direction', 'unknown')
                                                if direction == 'citing':
                                                    context_parts.append(f"        - Central node cites this paper")
                                                elif direction == 'cited':
                                                    context_parts.append(f"        - This paper cites central node")
                                                
                                                # Add any additional reference information
                                                for k, v in edge.items():
                                                    if k not in ['citing_paperid', 'cited_paperid', 'direction'] and v:
                                                        context_parts.append(f"        - {k}: {v}")
                                            
                                            elif edge_type == 'Collab':
                                                # Add collaboration information
                                                collab_count = edge.get('collaboration_count', edge.get('count', 1))
                                                context_parts.append(f"        - Collaboration count: {collab_count}")
                                                
                                                # Add any additional collaboration information
                                                for k, v in edge.items():
                                                    if k not in ['author1_id', 'author2_id', 'collaboration_count', 'count'] and v:
                                                        context_parts.append(f"        - {k}: {v}")
                        
                        if len(neighbor_list) > max_neighbors:
                            context_parts.append(f"    ... and {len(neighbor_list) - max_neighbors} more nodes")
                        context_parts.append("")
            
            # Add summary of edge statistics
            if edges:
                context_parts.append("Relationship Summary:")
                for edge_type, edge_list in edges.items():
                    if edge_list:
                        context_parts.append(f"  {edge_type}: {len(edge_list)} relationships")
                        
                        # Add special statistics for Reference and Collab
                        if edge_type == 'Reference':
                            citing_count = len([e for e in edge_list if e.get('direction') == 'citing'])
                            cited_count = len([e for e in edge_list if e.get('direction') == 'cited'])
                            context_parts.append(f"    - Papers cited by central node: {citing_count}")
                            context_parts.append(f"    - Papers citing central node: {cited_count}")
                        
                        elif edge_type == 'Collab':
                            total_collabs = sum([e.get('collaboration_count', e.get('count', 1)) for e in edge_list])
                            context_parts.append(f"    - Total collaboration instances: {total_collabs}")
                            context_parts.append(f"    - Unique collaborators: {len(edge_list)}")
                
                context_parts.append("")
            
            context_parts.append("=" * 50)
            context_parts.append("")
        
        return "\n".join(context_parts)

    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using LLM with question and graph context
        
        Args:
            question: Original question
            context: Formatted context from ego-graphs
            
        Returns:
            Generated answer
        """
        prompt = f"""You are an expert academic research assistant with access to a knowledge graph. Please provide a concise, direct answer to the following question based on the retrieved graph information.
    
        Question: {question}
    
        Graph Context:
        {context}
    
        Answer Format Guidelines:
        - For questions asking about NUMBERS/QUANTITIES (e.g., "How many papers cite...", "What is the citation count..."): 
          → Respond with ONLY the specific number (e.g., "78")
          
        - For questions asking about AUTHORS (e.g., "Who is the author...", "Who wrote...", "Who are the authors..."):
          → Respond with ONLY the author name(s) (e.g., "John Smith" or "John Smith, Jane Doe")
          
        - For questions asking about PAPER TITLES (e.g., "What is the title...", "Which paper..."):
          → Respond with ONLY the exact paper title (e.g., "Clinical Development of Leukocyte Cyclooxygenase 2 Activity")
          
        - For questions asking about INSTITUTIONS/AFFILIATIONS:
          → Respond with ONLY the institution name(s)
          
        - For questions asking about PUBLICATION DETAILS (year, journal, etc.):
          → Respond with ONLY the requested detail (e.g., "2001" for year, "Nature" for journal)
          
        - For questions asking about RELATIONSHIPS (collaborations, citations, etc.):
          → Use the graph context to provide specific relationship information
          
        - For other types of questions:
          → Provide a brief, direct answer focusing on the key information requested
    
        Important Rules:
        1. Be extremely concise - avoid explanations, background information, or elaboration
        2. Extract the exact information requested from the graph context
        3. Use the relationship information from connected nodes when relevant
        4. If the specific information is not available, respond with "Information not available"
        5. Do not include phrases like "Based on the retrieved information" or "According to the data"
        6. Just provide the direct answer
    
        Answer:"""
    
        try:
            answer = self._call_llm(prompt)
            return answer.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
