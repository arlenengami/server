import sys
import random
import string

class Field:
    def __init__(self, name, is_nullible):
        self.name = name
        self.is_nullible = is_nullible

class Field_int(Field):
    def __init__(self, name, size, is_unsigned, is_nullible):
        Field.__init__(self, name, is_nullible)
        assert size == 1 or size == 2 or size == 3 or size == 4 or size == 8
        self.size = size
        self.is_unsigned = is_unsigned
        if self.size == 1:
            self.max_value = (1<<7)-1
        elif self.size == 2:
            self.max_value = (1<<15)-1
        elif self.size == 3:
            self.max_value = (1<<23)-1
        elif self.size == 4:
            self.max_value = (1<<31)-1
        else:
            self.max_value = (1<<63)-1
    def get_type(self):
        if self.size == 1:
            t = "TINYINT"
        elif self.size == 2:
            t = "SMALLINT"
        elif self.size == 3:
            t = "MEDIUMINT"
        elif self.size == 4:
            t = "INT"
        else:
            t = "BIGINT"
        if self.is_unsigned:
            t += " UNSIGNED"
        if not self.is_nullible:
            t += " NOT NULL"
        return t
    def get_value(self):
        return random.randint(0, self.max_value)
    
    def next_field(self, name):
        if self.size == 1:
            new_size = 2
        elif self.size == 2:
            new_size = 3
        elif self.size == 3:
            new_size = 4
        elif self.size == 4:
            new_size = 8
        else:
            new_size = 8
        return Field_int(name, new_size, self.is_unsigned, self.is_nullible)

class Field_int_auto_inc(Field_int):
    def __init__(self, name, size, is_unsigned, is_nullible):
        Field_int.__init__(self, name, size, is_unsigned, is_nullible)
        self.next_value = 0
    def get_type(self):
        return Field_int.get_type(self)
    def get_value(self):
        v = self.next_value
        self.next_value += 1
        return v

class Field_char(Field):
    def __init__(self, name, size, is_binary, is_nullible):
        Field.__init__(self, name, is_nullible)
        assert 0 <= size and size < 256
        self.size = size
        self.is_binary = is_binary
    def get_type(self):
        if self.is_binary:
            t = "BINARY"
        else:
            t = "CHAR"
        t += "(%d)" % (self.size)
        if not self.is_nullible:
            t += " NOT NULL"
        return t
    def next_size(self):
        if self.size < 255:
            return self.size + 1
        return self.size
    def get_value(self):
        l = random.randint(1, self.size)
        s = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(l))    
        return "'%s'" % (s)

class Field_varchar(Field):
    def __init__(self, name, size, is_binary, is_nullible):
        Field.__init__(self, name, is_nullible)
        assert 0 <= size and size < 64*1024
        self.size= size
        self.is_binary = is_binary
    def get_type(self):
        if self.is_binary:
            t = "VARBINARY"
        else:
            t = "VARCHAR"
        t += "(%d)" % (self.size)
        if not self.is_nullible:
            t += " NOT NULL"
        return t;
    def get_value(self):
        l = random.randint(1, self.size)
        s = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(l))    
        return "'%s'" % (s)
    def next_size(self):
        if self.size < 64*1024:
            return self.size + 1
        return self.size
    def next_field(self, name):
        if self.size < 256:
            new_size = 256
        else:
            new_size = self.size + 1
        return Field_varchar(name, new_size, self.is_binary, self.is_nullible)

class Field_blob(Field):
    def __init__(self, name, size, is_nullible):
        Field.__init__(self, name, is_nullible)
        self.size = size
    def get_type(self):
        return "BLOB(%d)" % (self.size)
    def get_value(self):
        l = random.randint(1, self.size)
        s = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(l))    
        return "'%s'" % (s)

def main():
    experiments = 1000
    nrows = 10
    random.seed(0)
    header()
    for experiment in range(experiments):
        # generate a schema
        fields = create_fields()

        # create a table with the schema
        print create_table(fields)

        # insert some rows
        for r in range(nrows):
            print insert_row(fields)
        print "CREATE TABLE ti LIKE t;"
        print "ALTER TABLE ti ENGINE=myisam;"
        print "INSERT INTO ti SELECT * FROM t;"

        # compare tables
        print "let $diff_tables = test.t, test.ti;"
        print "source include/diff_tables.inc;"

        # change fixed column
        next_field = fields[0].next_field('')
        print "ALTER TABLE t CHANGE COLUMN a a %s;" % (next_field.get_type())
        print "ALTER TABLE ti CHANGE COLUMN a a %s;" % (next_field.get_type())
        
        # add some more rows

        # compare tables
        print "let $diff_tables = test.t, test.ti;"
        print "source include/diff_tables.inc;"

        # change variable column
        next_field = fields[3].next_field('')
        print "ALTER TABLE t CHANGE COLUMN d dd %s;" % (next_field.get_type())
        print "ALTER TABLE ti CHANGE COLUMN d dd %s;" % (next_field.get_type())        

        # add some more rows

        # compare tables
        print "let $diff_tables = test.t, test.ti;"
        print "source include/diff_tables.inc;"

        # cleanup
        print "DROP TABLE t, ti;"
        print
    return 0

def create_fields():
    fields = []
    fields.append(create_int('a'))
    fields.append(create_int('b'))
    fields.append(create_char('c'))
    fields.append(create_varchar('d'))
    fields.append(create_varchar('e'))
    fields.append(create_varchar('f'))
    fields.append(Field_blob('g', 100, 0))
    fields.append(Field_blob('h', 100, 0))
    fields.append(Field_int_auto_inc('id', 8, 0, 0))
    return fields

def create_int(name):
    int_sizes = [ 1, 2, 3, 4, 8]
    return Field_int(name, int_sizes[random.randint(0,len(int_sizes)-1)], random.randint(0,1), random.randint(0,1))

def create_char(name):
    return Field_char(name, random.randint(1, 100), random.randint(0,1), random.randint(0,1))

def create_varchar(name):
    return Field_varchar(name, random.randint(1, 100), random.randint(0,1), random.randint(0,1))

def create_table(fields):
    t = "CREATE TABLE t ("
    for f in fields:
        t += "%s %s, " % (f.name, f.get_type())
    t += "KEY(b), CLUSTERING KEY(e), PRIMARY KEY(id)"
    t += ");"
    return t

def insert_row(fields):
    t = "INSERT INTO t VALUES ("
    for i in range(len(fields)):
        f = fields[i]
        t += "%s" % (f.get_value())
        if i < len(fields)-1:
            t += ","
    t += ");"
    return t

def header():
    print "# generated from change_all.py"
    print "# test random column change on wide tables"
    print "--disable_warnings"
    print "DROP TABLE IF EXISTS t, ti;"
    print "--enable_warnings"
    print "SET SESSION TOKUDB_DISABLE_SLOW_ALTER=1;"
    print "SET SESSION DEFAULT_STORAGE_ENGINE='TokuDB';"
    print

sys.exit(main())
