#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y postgresql python-dev python-pip libpq-dev libyaml-dev bind9

# Add database and user to PostgreSQL
sudo -i -u postgres psql <<EOS
  CREATE USER turbine WITH PASSWORD 'soopersecret';
  CREATE DATABASE turbine_development OWNER turbine;
EOS

# Change PostgreSQL to allow all the things
echo "listen_addresses = '*'" >> /etc/postgresql/9.3/main/postgresql.conf
echo "host    all    all    all    trust" >> /etc/postgresql/9.3/main/pg_hba.conf

service postgresql restart

# Install dependencies for Turbine
pip install -r requirements.txt
pip install psycopg2

# Configure BIND
cat > /etc/bind/named.conf.options <<EOF
options {
	directory "/var/cache/bind";

	forwarders {
		8.8.8.8;
		8.8.4.4;
	};

	dnssec-validation no;

	auth-nxdomain no;    # conform to RFC1035
	listen-on-v6 { any; };
};
EOF

cat > /etc/bind/named.conf.local <<EOF
zone "team1.ksucdc.org" IN {
	type forward;
	forward only;
	forwarders {
		172.20.5.20;
	};
};

zone "team2.ksucdc.org" IN {
	type forward;
	forward only;
	forwarders {
		// 127.0.0.1;
	};
};
EOF

cat > /etc/resolvconf/resolv.conf.d/head <<EOF
nameserver 127.0.0.1
EOF

service bind9 reload
resolvconf -u
