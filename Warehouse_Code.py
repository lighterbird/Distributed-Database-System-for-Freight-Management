import mysql.connector
import tkinter as tk

class Task:
    def __init__(self, query, typ):
        self.query = query
        self.typ = typ

class Warehouse:
    def __init__(self, host, user, password, database):
        # initializing warehouse parameters
        self.waredet = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
            }
        self.maindet = {
            'host': "172.31.22.100",
            'user': "remote_user1",
            'password': "admin",
            'database': "main_server"
            }
        self.Warehouse_ID = -1
        self.Warehouse_Name = "None"
        self.status = {'main': "Inactive", 'warehouse': "Inactive"}
        self.main = None
        self.connection = None
        self.state = "wait"
        self.queue = []
        self.output = "No Output Yet"
        self.conn_status()

    def __delete__(self):
        # Delete connections if they do exist
        if self.status['main'] == 'Active':
            self.main.close()
        if self.status['warehouse'] == 'Active':
            self.connection.close()
    def conn_status(self):
        # Trying to make mainserver connection
        try:
            self.main = mysql.connector.connect(
                host = self.maindet['host'],
                user = self.maindet['user'],
                password = self.maindet['password'],
                database = self.maindet['database'],
                connect_timeout = 1 # 0.5 Second Timeout
            )
            self.status['main'] = "Active"
        except Exception as exc:
            print("Exception in connection: ", exc)
            self.main = None
            self.status['main'] = "Inactive"

        # Trying to make local connection
        try:
            self.connection = mysql.connector.connect(
                host = self.waredet['host'],
                user = self.waredet['user'],
                password = self.waredet['password'],
                database = self.waredet['database'],
                connect_timeout = 1 # 0.5 Second Timeout
            )
            self.status['warehouse'] = "Active"
            res = self.warehouse_query("SELECT * FROM WAREHOUSE")
            print(res)
            self.Warehouse_ID = res[1][0][0]
            self.Warehouse_Name = res[1][0][1]
        except Exception as exc:
            print("Exception in connecting warehouse: ", exc)
            self.connection = None
            self.status['warehouse'] = "Inactive"  
    def queries_from_mainserver(self):
        queries = self.warehouse_query("SELECT * FROM WAREHOUSECOMMUNICATE WHERE TYPE_OF_MESSAGE = 1")
        # print("queries = ", queries)
        self.warehouse_query("DELETE FROM WAREHOUSECOMMUNICATE WHERE TYPE_OF_MESSAGE = 1")
        if queries[0] == True and queries[1] != None:
            return queries[1]
        else:
            return []
    def nonqueries_from_mainserver(self):
        non_queries = self.warehouse_query("SELECT * FROM WAREHOUSECOMMUNICATE WHERE TYPE_OF_MESSAGE = 2 OR TYPE_OF_MESSAGE = 3 ")
        self.warehouse_query("DELETE FROM WAREHOUSECOMMUNICATE WHERE TYPE_OF_MESSAGE = 2 OR TYPE_OF_MESSAGE = 3")
        
        print("NON QUERIES: ", non_queries)
        
        if non_queries[0] == True and non_queries[1] != None:
            return non_queries[1]
        else:
            return []
    def processNonQuery(self, nonquery):
        current_task =self.queue[0]
        query = current_task.query
        task_type = current_task.typ
        q = query.split()

        print("Non Query: ", nonquery)
        
        if task_type == 1 and nonquery[1] == 2:
            self.output = self.format_results(eval(nonquery[0]))
        
        elif q[0].lower() == "insert" and q[2].lower() == "warehouseshipments" and nonquery[1] == 3:
            if nonquery[0] == "valid":
                self.warehouse_query(current_task.query)
                self.output = "Inserted Succesfully"
            else:
                self.output = "Not Valid"
        self.queue.pop(0)
    def processQuery(self):
        current_task =self.queue[0]
        query = current_task.query
        task_type = current_task.typ
        q = query.split()

        if task_type == 0: # Warehouse Query
            if q[0].lower() == "select":
                result = self.warehouse_query(query)
                if result[0] == True and result[1] != None:
                    self.output = self.format_results(result[1])
                else:
                    self.output = result[1]
                self.queue.pop(0) # Query completed
                self.state = "wait"

            elif q[0].lower() == "insert" and q[2].lower() == "warehouseshipments":
                print("*****************************")
                result =self.warehouse_query(query, roll_back = 1)
                if result[0] == True:
                    if self.status["main"] == "Active":
                        self.to_main_server(query)
                    else:
                        self.queue.pop(0) # Query completed
                        self.state = "wait"
                        self.output = "Main Server Not connected"
                else:
                    self.output = "Not valid"
                    self.queue.pop(0) # Query completed
                    self.state = "wait"
            
            else:
                print("&&&&&&&&&&&&&&&&&&&&&&&&")
                result =self.warehouse_query(query)
                if result[0] == True and result[1] != None:
                    self.output = self.format_results(result[1])
                else:
                    self.output = result[1]
                self.queue.pop(0) # Query completed
                self.state = "wait"
        
        elif task_type == 1: # Main Server Query
            if self.status["main"] == "Active":
                self.to_main_server(query)
                self.output = "Query Sent to Main Server"
            else:
                self.queue.pop(0) # Query completed
                self.state = "wait"
                self.output = "Main Server Not connected"

        elif task_type == 2: # Query From Main Server
            if q[0].lower() == "select":
                result =self.warehouse_query(query)
                self.to_main_server(result[1], 2)
            elif q[0].lower() == "insert" and q[2].lower() == "warehouseshipments":
                result =self.warehouse_query(query)
                if result[0] == True:
                    self.to_main_server("valid", 3)
                else:
                    self.to_main_server("invalid", 3)
            self.queue.pop(0) # Query completed
            self.state = "wait"
    def to_main_server(self, query, type = 1, to_terminal = True):
        # formatting the query
        query = query.replace("'", "''")

        # Display in Terminal if Required
        if to_terminal:
            print("Query being sent to Main Server: ", query)

        # Sending query to main server if main server is connected
        if self.status['main'] == 'Active':
            cursor = self.main.cursor()
            query = "INSERT INTO MainCommunicate VALUES (" \
                + str(self.Warehouse_ID) + ", \'" \
                + query + "\', " \
                + str(type) + "   );"
            cursor.execute(query)
            self.main.commit()
            cursor.close()
            return True
        else:
            print("Could Not Send Query: Main Server Not Connected")
            return False
    def warehouse_query(self, query, roll_back = 0, to_terminal = True):
        # Query to your own database
        if to_terminal:
            print("Query to Warehouse: ", query)

        # Only Proceed if connected successfully
        if self.status['warehouse'] == 'Active':
            try:
                cursor = self.connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                if roll_back == 0:
                    self.connection.commit()
                    cursor.close()
                    return [True, results]
                else:
                    cursor.close()
                    return [True, None]
            except Exception as exc:
                cursor.close()
                print("Error : ", exc)
                return [False, exc]
        else:
            return [False, "Warehouse Server Not Connected"]
    def format_results(self, results):
        result = ""
        for res in results:
            for col in res:
                result += str(col) + "  "
            result +=  "\n"
        return result

if __name__ == "__main__":
    # Warehouse Credentials
    host = "127.0.0.1"
    user = "remote_user1"
    password = "admin"
    database = "WarehouseA"

    # Create Object
    A = Warehouse(host, user, password, database)

    root = tk.Tk()
    root.title("Warehouse: " + A.Warehouse_Name)
    root.geometry("400x300")

    keywords = ["select", "insert", "update", "delete"]

    def button_warehouse_query():
        text1 = entry1.get()
        A.queue.append(Task(text1, 0)) # To be executed on warehouse
        entry1.delete(0, tk.END)

    def button_mainserver_query():
        text2 = entry2.get()
        A.queue.append(Task(text2, 1)) # To be executed in Main server
        entry2.delete(0, tk.END)

    def Update():
        # Update Connection status
        A.conn_status()

        # Take in Queries from main server
        Queries = A.queries_from_mainserver()
        for q in Queries:
            A.queue.append(Task(q[0], 2)) # To be run in warehouse and result sent to main server

        # State Based Behaviour
        if A.state == "wait":
            A.nonqueries_from_mainserver() # Clear all Non Queries
            if len(A.queue)!=0:
                A.state = "exe"
                A.processQuery()

        elif A.state == "exe":
            from_main = A.nonqueries_from_mainserver()
            print("Recieved From Main Server: ", from_main)

            if len(from_main) != 0:
                A.processNonQuery(from_main[0])
                A.state = "wait" 

            if len(A.queue) == 0:
                A.state = "wait"

        # Display
        if A.status["main"] == 'Active':
            labelconn_main.config(text = 'Main Server: Active', fg=  'green')
        else:
            labelconn_main.config(text = 'Main Server: Inactive', fg=  'red')
        if A.status["warehouse"] == 'Active':
            labelconn_warehouse.config(text = 'Warehouse Server: Active', fg=  'green')
        else:
            labelconn_warehouse.config(text = 'Warehouse Server: Inactive', fg=  'red')
        
        labeloutput.config(text = A.output)

        if A.state == "wait":
            labelstate.config(text = "Waiting For Query")
        else:
            labelstate.config(text = "Executing Query ...")
        
        root.after(1000, Update)

    # Labels
    labelheading0 = tk.Label(root, text="--------- Query Options ---------")
    labelheading1 = tk.Label(root, text="--------- State ---------")
    labelheading2 = tk.Label(root, text="--------- Output ---------")
    labelheading3 = tk.Label(root, text="--------- Connection Status ---------")
    
    labelstate = tk.Label(root, text=A.state)
    labeloutput = tk.Label(root, text="")
    labelconn_main = tk.Label(root, text="Main Server: ")
    labelconn_warehouse = tk.Label(root, text="Warehouse: ")
    
    # Buttons
    button1 = tk.Button(root, text="Warehouse Query", command=button_warehouse_query)
    button2 = tk.Button(root, text="Main Server Query", command=button_mainserver_query)

    # Text Fields
    entry1 = tk.Entry(root, width=60, font=("Arial", 8)) 
    entry2 = tk.Entry(root, width=60, font=("Arial", 8))
    
    # Pack the Labels
    labelheading0.pack()
    button1.pack()
    entry1.pack()
    button2.pack()
    entry2.pack()

    labelheading1.pack()
    labelstate.pack()

    labelheading2.pack()
    labeloutput.pack()
    
    labelheading3.pack()
    labelconn_main.pack()
    labelconn_warehouse.pack()

    root.after(1000, Update)
    root.mainloop()