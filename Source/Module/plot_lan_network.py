#File Import
import pcap_reader
import communication_details_fetch
import tor_traffic_handle
import malicious_traffic_identifier
#import device_details_fetch
import memory

import networkx as nx
#import matplotlib.pyplot as plt

from graphviz import Digraph
import threading
import os

from pyvis.network import Network

class plotLan:

    def __init__(self, filename, path, option="Tor", to_ip="All", from_ip="All"):
        self.directory = os.path.join(path, "Report")
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        options = option + "_" + to_ip.replace(".", "-") + "_" + from_ip.replace(".", "-")
        self.filename = os.path.join(self.directory, filename+"_"+options)

        self.styles = {
            'graph': {
                'label': 'PcapGraph',
                'fontsize': '16',
                'fontcolor': 'black',
                'bgcolor': 'grey',
                'rankdir': 'LR', # BT
                'dpi':'300',
                'size': '10, 10',
                'overlap': 'scale'
            },
            'nodes': {
                'fontname': 'Helvetica',
                'shape': 'circle',
                'fontcolor': 'black',
                'color': ' black',
                'style': 'filled',
                'fillcolor': 'yellow',
            }
        }

        self.sessions = memory.packet_db.keys()
        #device_details_fetch.fetchDeviceDetails("ieee").fetch_info()
        if option == "Malicious" or option == "All":
            self.mal_identify = malicious_traffic_identifier.maliciousTrafficIdentifier()
        if option == "Tor" or option == "All":
            self.tor_identify = tor_traffic_handle.torTrafficHandle().tor_traffic_detection()
        self.draw_graph(option, to_ip, from_ip)
    
    def apply_styles(self, graph, styles):
        graph.graph_attr.update(
            ('graph' in styles and styles['graph']) or {}
        )
        graph.node_attr.update(
            ('nodes' in styles and styles['nodes']) or {}
        )
        return graph

    def apply_custom_style(self, graph, color):
        style = {'edges': {
                'style': 'dashed',
                'color': color,
                'arrowhead': 'open',
                'fontname': 'Courier',
                'fontsize': '12',
                'fontcolor': color,
        }}
        graph.edge_attr.update(
            ('edges' in style and style['edges']) or {}
        )
        return graph

    def draw_graph(self, option="All", to_ip="All", from_ip="All"):
        #f = Digraph('network_diagram - '+option, filename=self.filename, engine="dot", format="png")
        #f.attr(rankdir='LR', size='8,5')
        if len(memory.lan_hosts) > 20:
            f = Digraph('network_diagram - '+option, filename=self.filename, engine="circo", format="png")
        else:
            f = Digraph('network_diagram - '+option, filename=self.filename, engine="dot", format="png")
        
        interactive_graph = Network(directed=True, height="750px", width="100%", bgcolor="#222222", font_color="white")
        interactive_graph.barnes_hut()
        vis_nodes = []
        vis_edges = []

        f.attr('node', shape='doublecircle')
        #f.node('defaultGateway')

        f.attr('node', shape='circle')

        print("Starting Graph Plotting")
        edge_present = False

        mal, tor, http, https, icmp, dns = 0, 0, 0, 0, 0, 0

        if option == "All":
            # add nodes
            for session in self.sessions:
                src, dst, port = session.split("/")

                #print(from_ip, to_ip, src, dst)
                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    # TODO: Improvise this logic below
                    # * graphviz graph is not very good with the ":" in strings
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst
                    
                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""
                    
                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    #if (curr_node, curr_node, title=curr_node, color="yellow") not in vis_nodes:
                    #    vis_nodes.append((curr_node, curr_node, title=curr_node, color="yellow"))
                    #if (destination, destination, title=destination, color="yellow") not in vis_nodes:
                    #    vis_nodes.append((destination, destination, title=destination, color="yellow"))

                    if curr_node != destination:
                        if session in memory.possible_tor_traffic:
                            f.edge(curr_node, destination, label='TOR: ' + str(map_dst) ,color="white")
                            tor += 1
                            #interactive_graph.add_edge(curr_node, destination, color="white", value=tor/100, smooth={type: "curvedCCW", roundness: 0.4})
                            interactive_graph.add_edge(curr_node, destination, color="white", smooth={"type": "curvedCW", "roundness": tor/10})
                            #if edge not in vis_edges:toor
                            #    vis_edges.append(edge)
                            if edge_present == False:
                                edge_present = True
                        elif session in memory.possible_mal_traffic:
                            f.edge(curr_node, destination, label='Malicious: ' + str(map_dst) ,color="red")
                            mal += 1
                            #interactive_graph.add_edge(curr_node, destination, color="red", value=mal/100, smooth={"type": "curvedCW", "roundness": 0.4})
                            interactive_graph.add_edge(curr_node, destination, color="red", smooth={"type": "curvedCW", "roundness": mal/10})
                            #if edge not in vis_edges:
                            #    vis_edges.append(edge)
                            if edge_present == False:
                                edge_present = True
                        else:
                            if port == "443":
                                f.edge(curr_node, destination, label='HTTPS: ' + map_dst +": "+dlabel, color = "blue")
                                https += 1
                                interactive_graph.add_edge(curr_node, destination, color="blue", smooth={"type": "curvedCCW", "roundness": https/10})
                                #if edge not in vis_edges:
                                #    vis_edges.append(edge)
                                if edge_present == False:
                                    edge_present = True
                            if port == "80":
                                f.edge(curr_node, destination, label='HTTP: ' + map_dst +": "+dlabel, color = "green")
                                http += 1
                                interactive_graph.add_edge(curr_node, destination, color="green", smooth={"type": "curvedCW", "roundness": http/10})
                                #if edge not in vis_edges:
                                #    vis_edges.append(edge)
                                if edge_present == False:
                                    edge_present = True
                            if port == "ICMP":
                                f.edge(curr_node, destination, label='ICMP: ' + str(map_dst) ,color="black")
                                icmp += 1
                                interactive_graph.add_edge(curr_node, destination, color="purple", smooth={"type": "curvedCCW", "roundness": icmp/10})
                                #if edge not in vis_edges:
                                #    vis_edges.append(edge)
                                if edge_present == False:
                                    edge_present = True
                            if port == "53":
                                f.edge(curr_node, destination, label='DNS: ' + str(map_dst) ,color="orange")
                                dns += 1
                                interactive_graph.add_edge(curr_node, destination, color="pink", smooth={"type": "curvedCW", "roundness": dns/10})
                                #if edge not in vis_edges:
                                #    vis_edges.append(edge)
                                if edge_present == False:
                                    edge_present = True

        elif option == "HTTP":
            for session in self.sessions:
                src, dst, port = session.split("/")

                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    # TODO: Improvise this logic below
                    # * graphviz graph is not very good with the ":" in strings
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""
                    
                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if port == "80" and curr_node != destination:
                        f.edge(curr_node, destination, label='HTTP: ' + str(map_dst)+": "+dlabel, color = "green")
                        http += 1
                        interactive_graph.add_edge(curr_node, destination, color="green", smooth={"type": "curvedCW", "roundness": http/10})
                        if edge_present == False:
                            edge_present = True

        elif option == "HTTPS":
            for session in self.sessions:
                src, dst, port = session.split("/")
                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    # TODO: Improvise this logic below
                    # * graphviz graph is not very good with the ":" in strings
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""
                    
                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if port == "443" and curr_node != destination:
                        f.edge(curr_node, destination, label='HTTPS: ' + str(map_dst)+": "+dlabel, color = "blue")
                        https += 1
                        interactive_graph.add_edge(curr_node, destination, color="blue", smooth={"type": "curvedCCW", "roundness": https/10})
                        if edge_present == False:
                            edge_present = True

        elif option == "Tor":
            for session in self.sessions:
                src, dst, port = session.split("/")
                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    # TODO: Improvise this logic below
                    # * graphviz graph is not very good with the ":" in strings
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""

                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if session in memory.possible_tor_traffic and curr_node != destination:
                        f.edge(curr_node, destination, label='TOR: ' + str(map_dst) ,color="white")
                        tor += 1
                        interactive_graph.add_edge(curr_node, destination, color="white", smooth={"type": "curvedCW", "roundness": tor/10})
                        if edge_present == False:
                            edge_present = True

        elif option == "Malicious":
            # TODO: would we need to iterate over and over all the session irrespective of the properties
            for session in self.sessions:
                src, dst, port = session.split("/")

                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    # TODO: Improvise this logic below
                    # * graphviz graph is not very good with the ":" in strings
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""

                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if session in memory.possible_mal_traffic and curr_node != destination:
                        f.edge(curr_node, destination, label='Malicious: ' + str(map_dst) ,color="red")
                        mal += 1
                        interactive_graph.add_edge(curr_node, destination, color="red", smooth={"type": "curvedCW", "roundness": mal/10})                 
                        if edge_present == False:
                            edge_present = True
            
        elif option == "ICMP":
            for session in self.sessions:
                src, dst, protocol = session.split("/")

                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""

                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if protocol == "ICMP" and curr_node != destination:
                        f.edge(curr_node, destination, label='ICMP: ' + str(map_dst) ,color="black")
                        icmp += 1
                        interactive_graph.add_edge(curr_node, destination, color="purple", smooth={"type": "curvedCCW", "roundness": icmp/10})        
                        if edge_present == False:
                            edge_present = True
    
        elif option == "DNS":
            for session in self.sessions:
                src, dst, port = session.split("/")
                if (src == from_ip and dst == to_ip) or \
                    (from_ip == "All" and to_ip == "All") or \
                        (to_ip == "All" and from_ip == src) or \
                            (to_ip == dst and from_ip == "All"):
                    if ":" in src:
                        map_src = src.replace(":",".")
                    else:
                        map_src = src
                    if ":" in dst:
                        map_dst = dst.replace(":", ".")
                    else:
                        map_dst = dst

                    # Lan Host
                    if memory.packet_db[session]["Ethernet"]["src"] not in memory.lan_hosts:
                        curr_node = map_src+"\n"+memory.packet_db[session]["Ethernet"]["src"].replace(":",".")
                        f.node(curr_node)
                    else:
                        curr_node = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["src"]]["node"]
                        f.node(curr_node)

                    # Destination
                    if dst in memory.destination_hosts:
                        if memory.destination_hosts[dst]["mac"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.destination_hosts[dst]["mac"]]["node"]
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                        else:
                            destination = memory.destination_hosts[dst]["mac"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = memory.destination_hosts[dst]["domain_name"]
                    else:
                        if memory.packet_db[session]["Ethernet"]["dst"] in memory.lan_hosts:
                            destination = memory.lan_hosts[memory.packet_db[session]["Ethernet"]["dst"]]["node"]
                            dlabel = ""
                        else:
                            destination = memory.packet_db[session]["Ethernet"]["dst"].replace(":",".")
                            destination += "\n"+"PossibleGateway"
                            dlabel = ""

                    # Interactive Graph on Beta, so for now add safety checks ( potential failures in python2)
                    try:
                        interactive_graph.add_node(str(curr_node), str(curr_node), title=str(curr_node), color="yellow")
                        interactive_graph.add_node(str(destination), str(destination), title=str(destination), color="yellow")
                    except Exception as e:
                        print("Interactive graph error occurred: "+str(e))

                    if port == "53" and curr_node != destination:
                        f.edge(curr_node, destination, label='DNS: ' + str(map_dst) ,color="orange")
                        dns += 1
                        interactive_graph.add_edge(curr_node, destination, color="pink", smooth={"type": "curvedCW", "roundness": dns/10})        
                        if edge_present == False:
                            edge_present = True

        if edge_present == False:
            f.attr(label="No "+option+" Traffic between nodes!",engine='circo', size="5, 5", dpi="300")

        self.apply_styles(f,self.styles)
            
        f.render()

        interactive_graph.save_graph(self.filename+".html")
                
def main():
    # draw example
    pcapfile = pcap_reader.PcapEngine('examples/torExample.pcap', "scapy")
    print("Reading Done....")
    details = communication_details_fetch.trafficDetailsFetch("sock")
    import sys
    print(sys.path[0])
    network = plotLan("test", sys.path[0])

#main()
