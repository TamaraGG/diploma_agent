import os
import asyncio
from dotenv import load_dotenv
from langchain_community.chains.graph_qa.base import GraphQAChain
from langchain_community.graphs import NetworkxEntityGraph
from langchain_community.llms.gigachat import GigaChat
from langchain_core.output_parsers import JsonOutputParser
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import UnstructuredRelation, examples
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from pyvis.network import Network

from src.rag.test_text import test_text

load_dotenv()
api_key = os.getenv("GIGACHAT_API_KEY")

llm = GigaChat(
    temperature=0,
    credentials=api_key,
    verify_ssl_certs=False
)

# Создаем кастомный системный промпт для GigaChat
system_prompt = """
You are a data scientist working for a company that is building a knowledge graph database. 
Your task is to extract information from data and convert it into a knowledge graph database.
Provide a set of Nodes in the form [head, head_type, relation, tail, tail_type].
It is important that the head and tail exists as nodes that are related by the relation. If you can't pair a relationship with a pair of nodes don't add it.
When you find a node or relationship you want to add try to create a generic TYPE for it that describes the entity you can also think of it as a label.
You must generate the output in a JSON format containing a list with JSON objects. Each object should have the keys: "head", "head_type", "relation", "tail", and "tail_type".
"""

system_message = SystemMessage(content=system_prompt)
parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

human_prompt = PromptTemplate(
    template="""
Examples:
{examples}

For the following text, extract entities and relations as in the provided example.
{format_instructions}\nText: {input}""",
    input_variables=["input"],
    partial_variables={
        "format_instructions": parser.get_format_instructions(),
        "node_labels": None,
        "rel_types": None,
        "examples": examples,
    },
)

human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)

chat_prompt = ChatPromptTemplate.from_messages(
    [system_message, human_message_prompt]
)

# Используем кастомный промпт при создании трансформатора
graph_transformer = LLMGraphTransformer(
    llm=llm,
    prompt=chat_prompt,  # КЛЮЧЕВОЙ ПАРАМЕТР!
    strict_mode=False  # Отключаем строгий режим для большей гибкости
)

text = test_text
documents = [Document(page_content=text)]

async def f():
    graph_documents = await graph_transformer.aconvert_to_graph_documents(documents)
    if graph_documents and len(graph_documents) > 0:
        print(f"Nodes: {graph_documents[0].nodes}")
        print(f"Relationships: {graph_documents[0].relationships}")
        visualize_graph(graph_documents)
    else:
        print("Не удалось извлечь граф из текста. Проверьте содержимое test_text.")

    graph = NetworkxEntityGraph()

    # Add nodes to the graph
    for node in graph_documents[0].nodes:
        graph.add_node(node.id)

    # Add edges to the graph
    for edge in graph_documents[0].relationships:
        graph._graph.add_edge(
            edge.source.id,
            edge.target.id,
            relation=edge.type,
        )
    chain = GraphQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True
    )
    question = """Какие есть актеры?"""
    chain.run(question)





def visualize_graph(graph_documents):
    """
    Visualizes a knowledge graph using PyVis based on the extracted graph documents.

    Args:
        graph_documents (list): A list of GraphDocument objects with nodes and relationships.

    Returns:
        pyvis.network.Network: The visualized network graph object.
    """
    # Create network
    net = Network(height="1200px", width="100%", directed=True,
                  notebook=False, bgcolor="#222222", font_color="white", filter_menu=True, cdn_resources='remote')

    nodes = graph_documents[0].nodes
    relationships = graph_documents[0].relationships

    # Build lookup for valid nodes
    node_dict = {node.id: node for node in nodes}

    # Filter out invalid edges and collect valid node IDs
    valid_edges = []
    valid_node_ids = set()
    for rel in relationships:
        if rel.source.id in node_dict and rel.target.id in node_dict:
            valid_edges.append(rel)
            valid_node_ids.update([rel.source.id, rel.target.id])

    # Track which nodes are part of any relationship
    connected_node_ids = set()
    for rel in relationships:
        connected_node_ids.add(rel.source.id)
        connected_node_ids.add(rel.target.id)

    # Add valid nodes to the graph
    for node_id in valid_node_ids:
        node = node_dict[node_id]
        try:
            net.add_node(node.id, label=node.id, title=node.type, group=node.type)
        except:
            continue  # Skip node if error occurs

    # Add valid edges to the graph
    for rel in valid_edges:
        try:
            net.add_edge(rel.source.id, rel.target.id, label=rel.type.lower())
        except:
            continue  # Skip edge if error occurs

    # Configure graph layout and physics
    net.set_options("""
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }
        }
    """)

    output_file = "knowledge_graph.html"
    try:
        net.save_graph(output_file)
        print(f"Graph saved to {os.path.abspath(output_file)}")
        return net
    except Exception as e:
        print(f"Error saving graph: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(f())