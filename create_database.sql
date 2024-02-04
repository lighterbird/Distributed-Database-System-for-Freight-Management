-- Main Server (Hub) Schema
CREATE TABLE Warehouses (
    WarehouseID INT PRIMARY KEY
);
CREATE TABLE Employees (
    EmployeeID INT PRIMARY KEY,
    WarehouseID INT
);
CREATE TABLE Shipments (
    ShipmentID INT PRIMARY KEY,
    StartWarehouseID INT,
    EndWarehouseID INT,
    StartDate DATE,
    EndDate DATE,
    Status VARCHAR(50),
    FOREIGN KEY (StartWarehouseID) REFERENCES Warehouses(WarehouseID),
    FOREIGN KEY (EndWarehouseID) REFERENCES Warehouses(WarehouseID)
);
CREATE TABLE Items (
    ItemID INT,
    WarehouseID INT,
    ShipmentID INT,
    Description VARCHAR(255),
    Quantity INT,
    WeightPerUnit DECIMAL(10, 2),
    VolumePerUnit DECIMAL(10, 2),
    PRIMARY KEY(ItemID, WarehouseID),
    FOREIGN KEY (ShipmentID) REFERENCES Shipments(ShipmentID)
);
CREATE TABLE MainCommunicate (
	Warehouse_ID INT PRIMARY KEY,
    Message VARCHAR(1000),
    type_of_message INT -- Query:1, Result:2, Comms: 3
);

-- Warehouse Server Schema
CREATE TABLE Warehouse (
    WarehouseID INT PRIMARY KEY,
    LocationName VARCHAR(255),
    City VARCHAR(255),
    Country VARCHAR(255)
);
CREATE TABLE WarehouseEmployees (
    EmployeeID INT PRIMARY KEY,
    FirstName VARCHAR(255),
    LastName VARCHAR(255),
    ContactEmail VARCHAR(255)
);
CREATE TABLE WarehouseShipments (
    ShipmentID INT PRIMARY KEY,
    StartWarehouseID INT,
    EndWarehouseID INT,
    StartDate DATE,
    EstimatedEndDate DATE,
    ActualEndDate DATE,
    Status VARCHAR(50),
    TotalWeight DECIMAL(10, 2),
    TotalVolume DECIMAL(10, 2)
);
CREATE TABLE WarehouseItems (
    ItemID INT PRIMARY KEY,
    ShipmentID INT,
    Description VARCHAR(255),
    Quantity INT,
    WeightPerUnit DECIMAL(10, 2),
    VolumePerUnit DECIMAL(10, 2),
    FOREIGN KEY (ShipmentID) REFERENCES WarehouseShipments(ShipmentID)
);
CREATE TABLE WarehouseCommunicate(
	Message VARCHAR(1000),
    type_of_message INT -- Query:1, Result:2, Comms: 3
);  

