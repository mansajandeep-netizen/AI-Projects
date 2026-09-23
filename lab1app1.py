# Lab1. Part 1 - Kings battles visualization in Game of Thrones (Streamlit web app)
# Import dependencies
import streamlit as st
import streamlit.components.v1 as components #to display the HTML code
import pandas as pd
from pyvis.network import Network #to create the graph as an interactive html object

nodeColors={
    0:"blue",
    1: "green",
    2: "orange",
    3: "purple",
    4: "gold",
    5:"red"
}

def data_load():
    data = pd.read_csv("data/game-of-thrones-battles.csv")
    battles_df=data.loc[:,['name','attacker_king','defender_king','attacker_size','defender_size']]
    #remove rows with any missing values (NaN)
    battles_df_cleaned=battles_df.dropna()
    return battles_df_cleaned

def buildGraph(battles_df_cleaned):
    net5kings = Network(
                bgcolor ="#242020",
                font_color = "white",
                height = "750px",
                width = "100%",
                directed = True, # we have directed graph
                cdn_resources = "remote")

    # nodes - unique names of all kings
    nodes=set(battles_df_cleaned['attacker_king']).union(set(battles_df_cleaned['defender_king']))
    net5kings.add_nodes(list(nodes))

    # edges - (attacking king, defending king) without repetitions
    edges = battles_df_cleaned[['attacker_king','defender_king']].values.tolist()
    unique_edges = set(tuple(edge) for edge in edges)

    # weights (N of battles) and titles (names of battles) of edges
    edges_w=battles_df_cleaned.groupby(['attacker_king','defender_king']).count()['name']
    edges_titles=battles_df_cleaned.groupby(['attacker_king','defender_king'])['name'].agg(', '.join)

    for edge in unique_edges:
        net5kings.add_edge(edge[0], edge[1], value=int(edges_w[edge]), title=edges_titles[edge])

    # node's value = 1 + N of kings this king has attacked, color depends on the value
    enemies_map = net5kings.get_adj_list()
    for node in net5kings.nodes:
        node["value"] = 1 + len(enemies_map[node["id"]])
        node["color"] = nodeColors[node["value"]]

    return net5kings, edges_w, edges_titles

def main():
    # Set header title
    st.title('Task1: Kings battles visualization in Game of Thrones')
    st.text('Interactive network of battles of the War of the Five Kings. '
            'Nodes are kings, an arrow goes from the attacking king to the defending king. '
            'Hover over an edge to see the battles.')

    battles_df_cleaned=data_load()
    net5kings, edges_w, edges_titles=buildGraph(battles_df_cleaned)

    tab1, tab2 = st.tabs(["Graph of battles of the War of 5 Kings", "Battles data"])

    with tab1:
        st.header('Lab1. Task1.')
        # Load HTML code of the graph in HTML component for display on Streamlit page
        components.html(net5kings.generate_html(), height = 800)

    with tab2:
        st.subheader('Battles (rows without missing values)')
        st.dataframe(battles_df_cleaned, hide_index=True)
        st.subheader('Number of battles between kings')
        summary=pd.DataFrame({'N of battles': edges_w, 'battles': edges_titles}).reset_index()
        st.dataframe(summary, hide_index=True)

if __name__ == '__main__':
    main()
