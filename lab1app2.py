# Lab1. Part 2 - infographic of relationships between characters in the Game of Thrones (Streamlit web app)
# Import dependencies
import json
import streamlit as st
import streamlit.components.v1 as components #to display the HTML code
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx #Networkx for creating graph data
from pyvis.network import Network #to create the graph as an interactive html object
from src.GameOfThronesGraphClass import GameOfThronesGraph

def data_load():
    with open("data/game-of-thrones-characters-groups.json", encoding="utf-8") as f:
        json_data = json.load(f)
    return GameOfThronesGraph(json_data['groups'])

def showHouses(GameOfThronesHouses):
    st.text("Game Of Thrones Houses:")
    visualisationData={}
    legendData=[]
    lines=[]
    for house in GameOfThronesHouses:
        lines.append(f"- {house}: Strength: {house.getStrength()}")
        visualisationData[house.name]=house.getStrength()
        legendData.append(house.name)
    st.markdown("\n".join(lines))

    #Configure your x and y values from the dictionary:
    x= list(visualisationData.keys())
    y=list(visualisationData.values())

    #Create the graph = create seaborn barplot
    fig, ax = plt.subplots()
    sns.barplot(x=x,y=y,ax=ax)
    ax.legend(legendData)
    sns.move_legend(ax, "upper left", bbox_to_anchor=(1.05, 1))
    ax.set(xlabel='Houses',
           ylabel='Strength (N family members)',
           title='Strength of GameOfThronesHouses')
    plt.setp(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)

def showMembers(GameOfThronesHouses):
    for house in GameOfThronesHouses:
        st.text(f"{house}. Our members:")
        st.markdown("\n".join(f"- {person}" for person in house))
        st.text(f"We have {house.getStrength()} family members!!!")

def buildGraph(GameOfThronesHouses):
    g = nx.Graph() # graph initialization

    # houses (strength is used as a node's size) and their family members as nodes
    for house in GameOfThronesHouses:
        if house.name!="Include":
            g.add_node(house.name, size=house.getStrength())
    for house in GameOfThronesHouses:
        if house.name!="Include":
            for person in house:
                g.add_node(person)

    # edges - connections between a House and its family members
    myEdges=[]
    for house in GameOfThronesHouses:
        if house.name!="Include":
            for person in house:
                myEdges.append((person, house.name))
    g.add_edges_from(myEdges)

    # different colors for different families
    colorKeys=[house.name for house in GameOfThronesHouses if house.name!="Include"]
    nodeColors=dict(zip(colorKeys, [tuple(int(c*255) for c in cs) for cs in sns.color_palette("husl", len(colorKeys))]))

    GameOfThronesNet = Network(
                bgcolor ="#242020",
                font_color = "white",
                height = "1000px",
                width = "100%",
                cdn_resources = "remote")
    # generate the graph
    GameOfThronesNet.from_nx(g)

    for node in GameOfThronesNet.nodes:
        if node["id"] in GameOfThronesHouses:
            # Convert RGB to hexadecimal string
            node["color"] = '#%02x%02x%02x' % nodeColors[node["id"]]
        else:
            for house in GameOfThronesHouses:
                if house.name !="Include":# apply the color of the House to this family member
                    if node["id"] in house:
                        node["color"] = '#%02x%02x%02x' % nodeColors[house.name]
    return GameOfThronesNet

def main():
    # Set header title
    st.title('Task2: infographic of relationships between characters in the Game of Thrones')

    GameOfThronesHouses=data_load()

    tab1, tab2, tab3 = st.tabs(["Game Of Thrones Houses", "Members of Houses", "Graph for Game Of Throne Houses"])

    with tab1:
        showHouses(GameOfThronesHouses)

    with tab2:
        showMembers(GameOfThronesHouses)

    with tab3:
        st.header('Lab1. Task2.')
        GameOfThronesNet=buildGraph(GameOfThronesHouses)
        # Load HTML code of the graph in HTML component for display on Streamlit page
        components.html(GameOfThronesNet.generate_html(), height = 1050)

if __name__ == '__main__':
    main()
