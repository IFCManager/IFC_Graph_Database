Link to paper: https://www.hindawi.com/journals/ace/2021/4913394/



# IFC and Sensor Database Example
Bridge_Example_Graph.ifc represent IFC model of a bridge monitoring example
sensordata.csv contains sensor data used in the example



IFC2Neo4j creates 4 .csv files which are to be imported to Neo4j using Neo4j Admin Import with the following command: 
> bin\neo4j-admin import --database=neo4j --nodes=import\Ifc_Node_root.csv --nodes=import\Ifc_Node_att.csv --nodes=import\Ifc_Node_nonroot.csv --relationships=import\Ifc_Connection_all.csv --delimiter="|"
