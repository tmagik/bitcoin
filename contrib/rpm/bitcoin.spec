%define _hardened_build 1
%global selinux_variants mls strict targeted

Name:     bitcoin
Version:  1.14.5
Release:  1%{?prerelease}%{?dist}
Summary:  Peer to Peer Cryptographic Currency

Group:    Applications/System
License:  MIT
URL:      http://bitcoin.org/
Source0:  https://github.com/btc1/%{name}/releases/download/v%{version}/%{name}-%{version}.tar.gz

BuildRoot:  %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:  miniupnpc-devel protobuf-devel openssl-devel
BuildRequires:  autoconf automake
BuildRequires:  checkpolicy selinux-policy-devel selinux-policy-doc
BuildRequires:  boost-devel libdb4-cxx-devel libevent-devel
BuildRequires:  libtool java

BuildRequires:  python2

BuildRequires:  python3-zmq zeromq-devel


%description
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.


%package libs
Summary:    Peer-to-peer digital currency


%package devel
Summary:   Peer-to-peer digital currency
Requires:  bitcoin-libs%{?_isa} = %{version}-%{release}


%package utils
Summary:    Peer-to-peer digital currency
Obsoletes:  bitcoin-cli <= 0.9.3


%package server
Summary:          Peer-to-peer digital currency
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
BuildRequires:    systemd
Requires(pre):    shadow-utils
Requires(post):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires(postun): /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires:   selinux-policy
Requires:   policycoreutils-python
Requires:   openssl-libs
Requires:	  bitcoin-utils%{_isa} = %{version}


%description libs
This package provides the bitcoinconsensus shared libraries. These libraries
may be used by third party software to provide consensus verification
functionality.

Unless you know need this package, you probably do not.


%description devel
This package contains the header files and static library for the
bitcoinconsensus shared library. If you are developing or compiling software
that wants to link against that library, then you need this package installed.

Most people do not need this package installed.


%description utils
Bitcoin is an experimental new digital currency that enables instant
payments to anyone, anywhere in the world. Bitcoin uses peer-to-peer
technology to operate with no central authority: managing transactions
and issuing money are carried out collectively by the network.

This package provides bitcoin-cli, a utility to communicate with and
control a Bitcoin server via its RPC protocol, and bitcoin-tx, a utility
to create custom Bitcoin transactions.


%description server
This package provides a stand-alone bitcoin-core daemon. For most users, this
package is only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
bitcoin-core node they use to connect to the network.

If you use the graphical bitcoin-core client then you almost certainly do not
need this package.

%package utils
Summary:	Bitcoin utilities
Group:		Applications/System

%description utils
This package provides several command line utilities for interacting with a
bitcoin-core daemon.

The bitcoin-cli utility allows you to communicate and control a bitcoin daemon
over RPC, the bitcoin-tx utility allows you to create a custom transaction, and
the bench_bitcoin utility can be used to perform some benchmarks.

This package contains utilities needed by the bitcoin-server package.


%prep
%setup -q
%patch0 -p1 -b .libressl
cp -p %{SOURCE10} ./bitcoin.conf.example
tar -zxf %{SOURCE1}
cp -p db-%{bdbv}.NC/LICENSE ./db-%{bdbv}.NC-LICENSE
mkdir db4 SELinux
cp -p %{SOURCE30} %{SOURCE31} %{SOURCE32} SELinux/


%build
CWD=`pwd`
cd db-%{bdbv}.NC/build_unix/
../dist/configure --enable-cxx --disable-shared --with-pic --prefix=${CWD}/db4
make install
cd ../..

./autogen.sh
%configure LDFLAGS="-L${CWD}/db4/lib/" CPPFLAGS="-I${CWD}/db4/include/" --with-miniupnpc --enable-glibc-back-compat %{buildargs}
make %{?_smp_mflags}

pushd SELinux
for selinuxvariant in %{selinux_variants}; do
	make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
	mv bitcoin.pp bitcoin.pp.${selinuxvariant}
	make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
popd


%install
make install DESTDIR=%{buildroot}

mkdir -p -m755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/bitcoind %{buildroot}%{_sbindir}/bitcoind

# systemd stuff
mkdir -p %{buildroot}%{_tmpfilesdir}
cat <<EOF > %{buildroot}%{_tmpfilesdir}/bitcoin.conf
d /run/bitcoind 0750 bitcoin bitcoin -
EOF
touch -a -m -t 201504280000 %{buildroot}%{_tmpfilesdir}/bitcoin.conf

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
cat <<EOF > %{buildroot}%{_sysconfdir}/sysconfig/bitcoin
# Provide options to the bitcoin daemon here, for example
# OPTIONS="-testnet -disable-wallet"

OPTIONS=""

# System service defaults.
# Don't change these unless you know what you're doing.
CONFIG_FILE="%{_sysconfdir}/bitcoin/bitcoin.conf"
DATA_DIR="%{_localstatedir}/lib/bitcoin"
PID_FILE="/run/bitcoind/bitcoind.pid"
EOF
touch -a -m -t 201504280000 %{buildroot}%{_sysconfdir}/sysconfig/bitcoin

mkdir -p %{buildroot}%{_unitdir}
cat <<EOF > %{buildroot}%{_unitdir}/bitcoin.service
[Unit]
Description=Bitcoin daemon
After=syslog.target network.target

[Service]
Type=forking
ExecStart=%{_sbindir}/bitcoind -daemon -conf=\${CONFIG_FILE} -datadir=\${DATA_DIR} -pid=\${PID_FILE} \$OPTIONS
EnvironmentFile=%{_sysconfdir}/sysconfig/bitcoin
User=bitcoin
Group=bitcoin

Restart=on-failure
PrivateTmp=true
TimeoutStopSec=120
TimeoutStartSec=60
StartLimitInterval=240
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF
touch -a -m -t 201504280000 %{buildroot}%{_unitdir}/bitcoin.service
#end systemd stuff

mkdir %{buildroot}%{_sysconfdir}/bitcoin
mkdir -p %{buildroot}%{_localstatedir}/lib/bitcoin

#SELinux
for selinuxvariant in %{selinux_variants}; do
	install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
	install -p -m 644 SELinux/bitcoin.pp.${selinuxvariant} %{buildroot}%{_datadir}/selinux/${selinuxvariant}/bitcoin.pp
done

%if %{_buildqt}
# qt icons
install -D -p share/pixmaps/bitcoin.ico %{buildroot}%{_datadir}/pixmaps/bitcoin.ico
install -p share/pixmaps/nsis-header.bmp %{buildroot}%{_datadir}/pixmaps/
install -p share/pixmaps/nsis-wizard.bmp %{buildroot}%{_datadir}/pixmaps/
install -p %{SOURCE100} %{buildroot}%{_datadir}/pixmaps/bitcoin.svg
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/bitcoin16.png -w16 -h16
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/bitcoin32.png -w32 -h32
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/bitcoin64.png -w64 -h64
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/bitcoin128.png -w128 -h128
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/bitcoin256.png -w256 -h256
%{_bindir}/convert -resize 16x16 %{buildroot}%{_datadir}/pixmaps/bitcoin256.png %{buildroot}%{_datadir}/pixmaps/bitcoin16.xpm
%{_bindir}/convert -resize 32x32 %{buildroot}%{_datadir}/pixmaps/bitcoin256.png %{buildroot}%{_datadir}/pixmaps/bitcoin32.xpm
%{_bindir}/convert -resize 64x64 %{buildroot}%{_datadir}/pixmaps/bitcoin256.png %{buildroot}%{_datadir}/pixmaps/bitcoin64.xpm
%{_bindir}/convert -resize 128x128 %{buildroot}%{_datadir}/pixmaps/bitcoin256.png %{buildroot}%{_datadir}/pixmaps/bitcoin128.xpm
%{_bindir}/convert %{buildroot}%{_datadir}/pixmaps/bitcoin256.png %{buildroot}%{_datadir}/pixmaps/bitcoin256.xpm
touch %{buildroot}%{_datadir}/pixmaps/*.png -r %{SOURCE100}
touch %{buildroot}%{_datadir}/pixmaps/*.xpm -r %{SOURCE100}

# Desktop File - change the touch timestamp if modifying
mkdir -p %{buildroot}%{_datadir}/applications
cat <<EOF > %{buildroot}%{_datadir}/applications/bitcoin-core.desktop
[Desktop Entry]
Encoding=UTF-8
Name=Bitcoin
Comment=Bitcoin P2P Cryptocurrency
Comment[fr]=Bitcoin, monnaie virtuelle cryptographique pair à pair
Comment[tr]=Bitcoin, eşten eşe kriptografik sanal para birimi
Exec=bitcoin-qt %u
Terminal=false
Type=Application
Icon=bitcoin128
MimeType=x-scheme-handler/bitcoin;
Categories=Office;Finance;
EOF
# change touch date when modifying desktop
touch -a -m -t 201511100546 %{buildroot}%{_datadir}/applications/bitcoin-core.desktop
%{_bindir}/desktop-file-validate %{buildroot}%{_datadir}/applications/bitcoin-core.desktop

# KDE protocol - change the touch timestamp if modifying
mkdir -p %{buildroot}%{_datadir}/kde4/services
cat <<EOF > %{buildroot}%{_datadir}/kde4/services/bitcoin-core.protocol
[Protocol]
exec=bitcoin-qt '%u'
protocol=bitcoin
input=none
output=none
helper=true
listing=
reading=false
writing=false
makedir=false
deleting=false
EOF
# change touch date when modifying protocol
touch -a -m -t 201511100546 %{buildroot}%{_datadir}/kde4/services/bitcoin-core.protocol
%endif

# man pages
install -D -p %{SOURCE20} %{buildroot}%{_mandir}/man1/bitcoind.1
install -p %{SOURCE21} %{buildroot}%{_mandir}/man1/bitcoin-cli.1
%if %{_buildqt}
install -p %{SOURCE22} %{buildroot}%{_mandir}/man1/bitcoin-qt.1
%endif

# nuke these, we do extensive testing of binaries in %%check before packaging
rm -f %{buildroot}%{_bindir}/test_*

%check
make check
srcdir=src test/bitcoin-util-test.py
test/functional/test_runner.py --extended

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%pre server
getent group bitcoin >/dev/null || groupadd -r bitcoin
getent passwd bitcoin >/dev/null ||
	useradd -r -g bitcoin -d /var/lib/bitcoin -s /sbin/nologin \
	-c "Bitcoin wallet server" bitcoin
exit 0


%post server
%systemd_post bitcoin.service
for selinuxvariant in %{selinux_variants}
do
	/usr/sbin/semodule -s ${selinuxvariant} -i \
		%{_datadir}/selinux/${selinuxvariant}/bitcoin.pp \
		&> /dev/null || :
done
# FIXME This is less than ideal, but until dwalsh gives me a better way...
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8332
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8333
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18332
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18333
/sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
/sbin/restorecon -R %{_localstatedir}/lib/bitcoin || :


%posttrans server
/usr/bin/systemd-tmpfiles --create


%preun server
%systemd_preun bitcoin.service


%postun server
%systemd_postun bitcoin.service
if [ $1 -eq 0 ] ; then
	# FIXME This is less than ideal, but until dwalsh gives me a better way...
	/usr/sbin/semanage port -d -p tcp 8332
	/usr/sbin/semanage port -d -p tcp 8333
	/usr/sbin/semanage port -d -p tcp 18332
	/usr/sbin/semanage port -d -p tcp 18333
	for selinuxvariant in %{selinux_variants}
	do
		/usr/sbin/semodule -s ${selinuxvariant} -r bitcoin \
		&> /dev/null || :
	done
	/sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
	[ -d %{_localstatedir}/lib/bitcoin ] && \
		/sbin/restorecon -R %{_localstatedir}/lib/bitcoin \
		&> /dev/null || :
fi


%files libs
%defattr(-,root,root,-)
%license COPYING
%doc doc/README.md doc/shared-libraries.md
%{_libdir}/libbitcoinconsensus.so*


%files devel
%defattr(-,root,root,-)
%license COPYING
%doc doc/README.md doc/developer-notes.md doc/shared-libraries.md
%{_includedir}/bitcoinconsensus.h
%{_libdir}/libbitcoinconsensus.a
%{_libdir}/libbitcoinconsensus.la
%{_libdir}/pkgconfig/libbitcoinconsensus.pc


%files utils
%defattr(-,root,root,-)
%license COPYING
%doc bitcoin.conf.example doc/README.md
%{_bindir}/bitcoin-cli
%{_bindir}/bitcoin-tx
%{_mandir}/man1/bitcoin-cli.1*
%{_mandir}/man1/bitcoin-tx.1*


%files server
%defattr(-,root,root,-)
%license COPYING
%doc doc/README.md doc/REST-interface.md doc/bips.md doc/dnsseed-policy.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md doc/zmq.md
%dir %attr(750,bitcoin,bitcoin) %{_localstatedir}/lib/bitcoin
%dir %attr(750,bitcoin,bitcoin) %{_sysconfdir}/bitcoin
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/sysconfig/bitcoin
%doc SELinux/*
%{_sbindir}/bitcoind
%{_unitdir}/bitcoin.service
%{_tmpfilesdir}/bitcoin.conf
%{_mandir}/man1/bitcoind.1*
%{_datadir}/selinux/*/bitcoin.pp


%changelog
* Fri Jul 21 2017 Ismael Bejarano <ismael.bejarano@coinfabrik.com> 1.14.5-1
- Update version for btc1 1.14.5
- Remove duplicate dependency line

* Mon Jul 10 2017 Ismael Bejarano <ismael.bejarano@coinfabrik.com> 1.14.3-1
- Packages for btc1 1.14.3 based on packages from https://www.ringingliberty.com/bitcoin/
