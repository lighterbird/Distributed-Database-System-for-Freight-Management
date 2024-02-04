import mysql.connector
import time
import tkinter as tk

class Main_Server:
    def __init__(self):
        self.main = mysql.connector.connect(
            host="localhost",
            user="remote_user1",
            password="admin",
            database="main_server"
        )

        # possible states : wait(waiting) , exe(executing)
        self.state = "wait"
        self.expected_id = -1
        self.current_query = None

        self.connections = {} # all connections
        self.connections_info = {} # connection info

        self.connections_info[1] = {
            "host" : "172.31.43.82",
            "user" : "remote_user3",
            "password" : "admin",
            "database" : "warehousea"
        }

        self.connections_info[2] = {
            "host" : "172.31.53.207",
            "user" : "remote_user3",
            "password" : "admin",
            "database" : "warehouseb"
        }

        self.connections_info[3] = {
            "host" : "172.31.53.207",
            "user" : "remote_user4",
            "password" : "admin",
            "database" : "warehousec"
        }

        for i, conn_info in self.connections_info.items():
            self.connections[i] = None

            try:
                connection = mysql.connector.connect(
                    host = conn_info['host'],
                    user = conn_info['user'],
                    password = conn_info['password'],
                    database = conn_info['database'], 
                    connect_timeout = 1
                )
                self.connections[i] = connection

            except:
                pass

        self.output = "*********************"

        # self.mainserver_query("DELETE FROM MainCommunicate")

    def display_connections(self):
        conn_status = []
        for i, conn in self.connections.items():

            try:
                connection = mysql.connector.connect(
                    host = self.connections_info[i]['host'],
                    user = self.connections_info[i]['user'],
                    password = self.connections_info[i]['password'],
                    database = self.connections_info[i]['database'],
                    connect_timeout = 1
                )
                self.connections[i] = connection
                conn_status.append((f"{self.connections_info[i]['database']} : Active",'green'))

            except:
                self.connections[i] = None
                conn_status.append((f"{self.connections_info[i]['database']} : Inactive",'red'))

        return conn_status
    
    def format_results(self, results):
        result = ""
        for res in results:
            for col in res:
                result += str(col) + "  "
            result +=  "\n"
        return result
    
    def __delete__(self):
        self.main.close()

        for conn in self.connections:
            if conn != None:
                conn.close()

    def to_warehouse(self, warehouse_id, query, type = 1):
        print("***** to_warehouse *****")
        print("query: ", query)
        
        try:
            query = query.replace("'", "''")
            cursor = self.connections[warehouse_id].cursor()
            query = "INSERT INTO WarehouseCommunicate VALUES (\'" + str(query) + "\' , "+ str(type) + ");"
            print("type : " , str(type))
            cursor.execute(query)
            self.connections[warehouse_id].commit()
            cursor.close()

        except Exception as exc:
            print(f"Error : {exc}")
            return (-1, exc)

    def from_warehouse(self, expected_id = -1):

        if self.state == 'wait':
            results = self.mainserver_query("SELECT * FROM MainCommunicate")

            if len(results) == 0:
                return -1

            else:
                result = results[0]
                self.mainserver_query("DELETE FROM MainCommunicate WHERE WAREHOUSE_ID = " + str(result[0]) + ";")
                return result

        elif self.state == 'exe':
            if expected_id != -1:
                results = self.mainserver_query(f"SELECT * FROM MainCommunicate WHERE warehouse_id = {str(expected_id)} AND type_of_message = 3")

                if len(results) == 0:
                    return -1
                
                else:
                    self.mainserver_query(f"DELETE FROM MainCommunicate WHERE warehouse_id = {str(expected_id)} AND type_of_message = 3")
                    return results[0]
            else:
                return -1

    def process_warehouse_query(self, query):
        warehouse_id = query[0]
        query = query[1]
        q = query.split()

        if self.state == "wait":
            self.state = "exe"
            if q[0].lower() == "select":
                results = self.mainserver_query(query)
                self.to_warehouse(int(warehouse_id), str(results), 2)
                self.state = "wait"

            elif q[0].lower() == "insert" and q[2].lower() == "warehouseshipments":
                tmp1 = query.split('(')
                tmp2 = tmp1[1].split(')')
                values = tmp2[0].split(',')

                for i in range(len(values)):
                    values[i] = values[i].strip()

                # Now values list contains all the values of the query
                main_query = "INSERT INTO SHIPMENTS VALUES(" + values[0] + ", " \
                        + values[1] + ", " \
                        + values[2] + ", " \
                        + values[3] + ", " \
                        + "NULL" + ", " \
                        + values[6] \
                        + ");"

                print("Main query: " , main_query)
                result = self.mainserver_query(main_query, roll_back = 1)

                if(result[0] == -1):
                    print("Couldn't insert in warehouseshipments")
                    print("Error: ", result[1])
                    self.to_warehouse(int(warehouse_id), "invalid", 3)
                    self.state = "wait"

                else:
                    # Now to update in destination warehouse
                    dest_warehouse = int(values[2])
                    if(self.connections[dest_warehouse] == None):
                        print("Couldn't insert in warehouseshipments")
                        print(f"Error: Destination ===> {self.connections_info[dest_warehouse]['database']} not connected")
                        self.to_warehouse(int(warehouse_id), "invalid", 3)
                        self.state = "wait"

                    else:
                        self.to_warehouse(dest_warehouse, query, 1)
                        self.expected_id = dest_warehouse
                        self.current_query = query
    
        elif self.state == "exe":
            if self.expected_id !=-1:
                if query == "valid":

                    query = self.current_query
                    tmp1 = query.split('(')
                    tmp2 = tmp1[1].split(')')
                    values = tmp2[0].split(',')

                    for i in range(len(values)):
                        values[i] = values[i].strip()

                    # Now values list contains all the values of the query
                    main_query = "INSERT INTO SHIPMENTS VALUES(" + values[0] + ", " \
                            + values[1] + ", " \
                            + values[2] + ", " \
                            + values[3] + ", " \
                            + "NULL" + ", " \
                            + values[6] \
                            + ");"

                    print("Main query: " , main_query)
                    result = self.mainserver_query(main_query)

                    self.to_warehouse(int(values[1]), "valid", 3)

                else:
                    query = self.current_query
                    tmp1 = query.split('(')
                    tmp2 = tmp1[1].split(')')
                    values = tmp2[0].split(',')
                    
                    self.to_warehouse(int(values[1]), "invalid", 3)
            self.current_query = None
            self.expected_id = -1
            self.state = "wait"
                   
                
    def mainserver_query(self, query, roll_back = 0):
        # print("***** mainserver_query *****")
        # print("Query: " , query)
        # print()

        try:
            cursor = self.main.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            self.main.commit()
            cursor.close()

            if(roll_back == 0):
                return results

            else:
                self.rollback(query)
                return "valid"

        except Exception as exc:
            print(f"Error : {exc}")
            return (-1, exc)

    def rollback(self, query):
        print("***** rollback *****")
        print("Query: " , query)
        print()

        q1 = query.split()
        table = q1[2]

        # pk = {"shipments": , "warehouseshipments": , }
        pk = f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'"
        result = self.mainserver_query(pk)[0]

        q2 = query.split('(')
        q3 = q2[-1].split(')')
        q4 = q3[0].split(',')

        primary_key = q4[0]

        del_query = f"DELETE FROM {table} WHERE {result[4]} = {primary_key}"
        print("Delete Query: ", del_query)
        print()

        self.mainserver_query(del_query)


if __name__ == "__main__":
    A = Main_Server()
    # print("CHECKPOINT 1")
    root = tk.Tk()
    root.title("Main Server")
    root.geometry("400x300")
    # print("CHECKPOINT 2")

    # def button_warehouse_query():
    #     label.config(text="Executing...")
    #     text1 = entry1.get()
    #     result = A.warehouse_query(text1)
    #     labeloutput.config(text = result)
    #     entry1.delete(0, tk.END)
    #     label.config(text="Query Options")

    # def button_mainserver_query():
    #     label.config(text="Executing...")
    #     text2 = entry2.get()
    #     A.to_main_server(text2)
    #     entry2.delete(0, tk.END)
    #     label.config(text="Query Options")

    def update():

        # print("CHECKPOINT 3")
        state_text = ""
        if A.state == 'wait':
            state_text = "Waiting for query"
            result = A.from_warehouse()
            if result != -1:
                A.output = result
                A.process_warehouse_query(result)

        elif A.state == 'exe':
            state_text = "Executing query ..."
            result = A.from_warehouse(A.expected_id)
            if result != -1:
                A.process_warehouse_query(result)
            
            # label.config(text="Query Options")

        connection_status = A.display_connections()
        for i, stat in enumerate(connection_status):
            status[i].config(text = connection_status[i][0], fg = connection_status[i][1])
        labeloutput.config(text = A.output)
        label_state.config(text = state_text)
        root.after(1000, update)

    # Labels
    label_heading_0 = tk.Label(root, text="===== State =====")
    label_heading_0.pack()

    label_state = tk.Label(root, text="")
    label_state.pack()

    label_heading_1 = tk.Label(root, text="===== Query Recieved Displayed Here =====")
    label_heading_1.pack()

    labeloutput = tk.Label(root, text="")
    labeloutput.pack()

    label_heading_2 = tk.Label(root, text="===== Connection Status =====")
    label_heading_2.pack()

    # print("CHECKPOINT 4")

    status = []
    for conn in A.connections:
        status.append(tk.Label(root, text = ""))
        status[-1].pack()   

    # print("CHECKPOINT 5") 

    # # Buttons
    # button1 = tk.Button(root, text="Warehouse Query", command=button_warehouse_query)
    # button1.pack()
    # button2 = tk.Button(root, text="Main Server Query", command=button_mainserver_query)
    # button2.pack()

    # # Text Fields
    # entry1 = tk.Entry(root, width=30, font=("Arial", 12))
    # entry1.pack()
    # entry2 = tk.Entry(root, width=30, font=("Arial", 12))
    # entry2.pack()

    # root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(1000, update)
    root.mainloop()

    # print("CHECKPOINT 6")