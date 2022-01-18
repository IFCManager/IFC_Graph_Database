############   Convert IFC express schema to Python lists   ############

schema = open("IFC4.express schema.txt","r")

#Bring schema into python as list
entities = []
entities_1=[]
#Read lines and append everything between entity and end_entity
for line in schema:
    
    #If the line start with entity, clear list of entities_1, so it start saving from the start of the entity to the end
    if line[:6] == "ENTITY":
        entities_1=[]
    
    #Always append lines to the entities_1 list
    entities_1.append(line.replace("\n","").replace("\t",""))
    
    #When the line comes to "end_entity" then append the list to actual entities list
    if line[:10] == "END_ENTITY":
        entities.append(entities_1)
        
#for i in entities:
    #for j in i:
        #print(j)


############   Parsing IFC express schema of separate express entities  ############

import re

parsed_entities=[]

for ent in entities:
    ent_parsed = []
    
    ### If last character (";") of first element ("ENTITY Ifcperson;"), then approach differenty, 
    ### since those are not in the hiearchy, don't have sub or super type
    if ent[0][-1] ==";":
        #[7:] removes ENTITY at the start, [:-1] removes \n at the end and replace removes ";"
        ent_parsed.append(ent[0][7:][:-1].replace(";",""))
        ent_parsed.append("No")   #These ifc types are not abstract
        ent_parsed.append(None)   #These ifc types are not subtypes or supertypes

        # Pattern here is that attributes will have tab "\t" in front of string, which was removed in previous step
        # and where it says " DERIVE" or " WHERE" will have a space " " in front, so when we first encounter " "
        # at the front then we break the loop.
        # ent[1:-2] takes the list without the first and the last two elements from the list
        for att in ent[1:-2]:
            att_split=[]
            # break when we encounter that the first character of the string is space " "
            if att[0] == " ":
                break
            att_split=att.replace(";","").split(" : ")
            findifc=re.search('Ifc(.*)',att_split[1])
            att_split[1]=findifc[0] if findifc != None else att_split[1]
            ent_parsed.append(att_split)
    
    ### Else parse all other entities, which have subtypes and do not have ";" at the end
    else:
        # First item in list is entity name
        ent_parsed.append(ent[0][7:])
        
        # Second item check if it is abstarct and append either "yes" or "no"
        if ent[1][1:5] == "ABST":
            ent_parsed.append("yes")
        else:
            ent_parsed.append("No")

        #Append None for the third element, if there is subtype, then override it    
        ent_parsed.append(None)
        
        # Iterate over all lines in entity without first and last two
        for att in ent[1:-2]:
            
            # If line start with "SUB" as in SUBTYPE of (ifc...) then find and replace None with the name inside parenthesis
            if att[1:4] == "SUB":
                ent_parsed[2] = re.findall('\(([^)]+)\)',att)[0]

            # Find all items that have " : " in the middle and ";" at the end, which signifies an attribute
            # Append said attribute after it is split and cleaned
            if re.search(r'(.*) \: (.*);', att):
                att_split=[]
                att_split=att.replace(";","").split(" : ")
                findifc=re.search('Ifc(.*)',att_split[1])
                att_split[1]=findifc[0] if findifc != None else att_split[1]
                ent_parsed.append(att_split)
            
            # If we encounter words INVERSE or WHERE or DERIVE or UNIQUE then break the loop, since attributed are before them
            if att[1:8] == "INVERSE" or att[1:7] == "WHERE" or att[1:8] == "DERIVE" or att[1:8] == "UNIQUE":
                break
    
    #Append parsed list of entities to a grouped list of all entities
    parsed_entities.append(ent_parsed)


############   Adding attributes to subtypes from the supertypes   ############

ent_names=[i[0] for i in parsed_entities]
entities_with_attributes=[]
ent_att=[]

#Loop over all entities and insert the attributes from the hiearchy and save in new list, which will be used for dictionary
for entity in parsed_entities:
    
    # Start with the current entity as the iterated entity
    ent_att=list(entity)
    current_entity=entity

    # Loop until the current entity has 'None' under subtypes
    while current_entity[2] != None:

        # Get the index of supertype of current entity
        # Replace current entity with the supertype of it by using getting it from the list with the index
        en = ent_names.index(current_entity[2])
        current_entity = parsed_entities[en]
        
        # Check if it has attributes, if it has not if will be empty list
        if current_entity[3:] != []:
            #Insert attributes of all supertype entites to the first entity
            for at in reversed(current_entity[3:]):
                ent_att.insert(3,at)
    
    entities_with_attributes.append(ent_att)
    
    
#print(entities_with_attributes)


############   Creating a dictionary of IFC express entities   ############

IfcEntity_dict={}    # Master dictionary -> IfcEntity_dict[IfcWall] ifc entries 
dictstr=[]

# Run commands to create dictionaries and save them to a list or a file
for e in entities_with_attributes:
    
    # Ignore abstract entities and entities without attributes for dictonary
    if e[1] == 'No' and e[3:] != []:
        
        # Create strings with commands for dictionaries and the names are ALL UPPER CASE so it matches ifc files
        dictstr = "IfcEntity_dict['" + str(e[0].upper()+"'] = {" )
        for attr in e[3:]:
            dictstr = dictstr + "'" + attr[0] + "' : '" + attr[1] +"', "
        dictstr = str(dictstr[:-2] + "}")
        
        # Run commands for dictionary
        exec(dictstr)




############   Functions for parsing IFC file   ############

def LINE_reader(file):
    #Reads only IFC lines, which have "#" infront.
    
    for line in file:   
        if line[0][0] == '#':
            yield line

def SPLIT_line(line):
    
    import re
    
    
    IFC_split = line.replace("= ","&,&").replace("(","&,&",1).split("&,&")
    IFC_split[0] = IFC_split[0]
    IFC_split[2] = IFC_split[2][:-3]

    #Splits attributes for commas "," everywhere, except inside parentheses "()" > ['$','$','(#1,#2)']
    Attributes = re.split(r"\,(?![^()]*\))(?![^'(\.)']*\',)",IFC_split[2])
    
    # \,(?![^'(\.)']*\',)  match "," except in single quotes ''   #There might be special cases where this does not work
    # \,(?![^()]*\))       match "," except in parenthesis ()

    for n in range(len(Attributes)):
            
            
        #Looks for nested IFC objects > #5175= IFCPROPERTYSINGLEVALUE('Reference',$,IFCIDENTIFIER('8mm Head'),$);
        if str(Attributes[n]).find("IFC") == 0:
            Attributes[n]=Attributes[n].replace(")","").split("(")
        
        else:
            #Looks for nested attributes > ($,$,(#1,#2)) and makes a nested list > [$,$,[#1,#2]]            
            #Find if an list element contains parentheses "()" so that its content gets split into a nested list
            NestedAtt=re.findall("\(([^)]*)\)(?![^'(\.)']*\')", Attributes[n])
            
            #Splits only elements inside "()"
            if NestedAtt != []:
                Attributes[n] = NestedAtt[0].split(",")
    
    IFC_split[2] = Attributes
    return IFC_split

def STEP_parser(path_file):
    
    
    f=open(path_file,"r") 
    
    for line in LINE_reader(f):

        yield SPLIT_line(line)


############   Exporting for Noe4j Admin Import   ############

### IFC FILE PATH
ifc_path = "example.ifc"
### IFC FILE PATH

Node_root = open("Ifc_Node_root.csv","w")
Node_att = open("Ifc_Node_att.csv","w")
Node_nonroot = open("Ifc_Node_nonroot.csv","w")
Connection = open("Ifc_Connection_all.csv","w")


#Headers for the csv files, 1) file for rooted entities, 2) for attributes, 3) for non_rooted entities and 4) for connections
header_root = "IfcId:ID|:LABEL|GlobalId|Name|Description\n"
header_att = "IfcId:ID|:LABEL|Value\n"
header_non_root = "IfcId:ID|:LABEL\n"
header_conn = ":START_ID|:END_ID|:TYPE|order:int\n"

Node_root.write(header_root)
Node_att.write(header_att)
Node_nonroot.write(header_non_root)
Connection.write(header_conn)


for ifc in STEP_parser(ifc_path):
    
    # List of dictionary keys and values for specific entity in a loop
    keys = list(IfcEntity_dict[ifc[1]].keys())
    values = list(IfcEntity_dict[ifc[1]].values())
    
    # Check if they have GlobalId, then they are rooted classes
    if "GlobalId" in IfcEntity_dict[ifc[1]]:
        
        # For nodes that are derived from IfcRoot (they contain GlobalId), take their name and first 4 attributes, which are
        # GlobalId, OwnerHistory, Name, Description

        # Write node based on an entity and a connection to Owner History
        neo_root = str(ifc[0]+"|"+ifc[1]+"|"+ifc[2][0]+"|"+ifc[2][2]+"|"+ifc[2][3]+"\n").replace("*","").replace("$","")
        neo_conn = ifc[0]+"|"+ifc[2][1]+"|"+keys[1]+"|"+"1"+"\n"  #Owner History
        Node_root.write(neo_root.replace("'",""))
        Connection.write(neo_conn)
        
        # Loop over attributes with item and number from 5th attribute forward "[4:]"
        for n,att in enumerate(ifc[2][4:]):
            
            # If an single attribute is a sublist then loop over that sublist
            if isinstance(att,list):
                
                # Currently it is a simple solution to just save a sublist as an single value string
                neo_att = ifc[0]+"_"+str(n+4)+"|"+values[n+4]+"|"+str(att)+"\n"
                neo_conn = ifc[0]+"|"+ifc[0]+"_"+str(n+4)+"|"+keys[n+4].upper()+"|"+str(n+4)+"\n"
                Node_att.write(neo_att.replace("'",""))
                Connection.write(neo_conn)

                # If the sublist has connection then loop over them and connect it to the subnode
                for n2,att2 in enumerate(att):
                    if att2[0] == "#":
                        neo_conn = ifc[0]+"_"+str(n+4)+"|"+att2+"|"+keys[n+4].upper()+"|"+str(n2)+"\n"
                        #print(neo_conn)
                        Connection.write(neo_conn)
                        

            # If an attribute is not a list then just create a node and connection to that node
            else:
                
                # If it contains a connection label with "#" than create a connection
                if att[0] == "#":
                    neo_conn = ifc[0]+"|"+att+"|" + keys[n+4].upper()+"|"+ str(n+4)+"\n"
                    Connection.write(neo_conn)
                    
                # Else create a node and a connection to that node
                else:
                    neo_att = str(ifc[0]+"_"+str(n+4)+"|"+values[n+4]+"|"+str(att)+"\n") #.replace("*","").replace("$","")
                    neo_conn = ifc[0] +"|"+ifc[0]+"_"+str(n+4)+"|"+keys[n+4].upper()+"|"+str(n+4)+"\n"
                    Node_att.write(neo_att.replace("'",""))
                    Connection.write(neo_conn)
            
            
    # If it does not have GlobalId, do everything the same, except dont start with attributes from the 5th onward
    else:

        neo_non_root = ifc[0]+"|"+ifc[1]+"\n"
        #print(neo_non_root)
        Node_nonroot.write(neo_non_root.replace("'",""))
        
        for n,att in enumerate(ifc[2]):

            if isinstance(att,list):
                print(ifc[0],values[n],n)
                neo_att = ifc[0]+"_"+str(n)+"|"+values[n]+"|"+str(att)+"\n"
                neo_conn = ifc[0]+"|"+ifc[0]+"_"+str(n)+"|"+keys[n].upper()+"|"+str(n)+"\n"
                Node_att.write(neo_att.replace("'",""))
                Connection.write(neo_conn)

                for n2,att2 in enumerate(att):
                    if  att2 != "" and att2[0] == "#":
                        neo_conn = ifc[0]+"_"+str(n)+"|"+att2+"|"+keys[n].upper()+"|"+str(n2)+"\n"
                        Connection.write(neo_conn)
                              
            else:
                if att[0] == "#":
                    neo_conn = ifc[0]+"|"+att+"|" + keys[n].upper()+"|"+ str(n)+"\n"
                    Connection.write(neo_conn)
                    
                else:
                    neo_att = str(ifc[0]+"_"+str(n)+"|"+values[n]+"|"+str(att)+"\n") #.replace("*","").replace("$","")
                    neo_conn = ifc[0] +"|"+ifc[0]+"_"+str(n)+"|"+keys[n].upper()+"|"+str(n)+"\n"
                    Node_att.write(neo_att.replace("'",""))
                    Connection.write(neo_conn)
                    
print("done")   




