-- Create hospital_user in Oracle
CREATE USER hospital_user IDENTIFIED BY hospital_pass;
GRANT CONNECT, RESOURCE, DBA TO hospital_user;
GRANT UNLIMITED TABLESPACE TO hospital_user;
EXIT;
