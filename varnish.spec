%define major 1
%define libname %mklibname varnish %{major}
%define develname %mklibname varnish -d

Summary:	Varnish is a high-performance HTTP accelerator
Name:		varnish
Version:	3.0.3
Release:	17
License:	BSD
Group:		System/Servers
URL:		https://www.varnish-cache.org/
Source0:	http://repo.varnish-cache.org/source/varnish-%{version}.tar.gz
Source1:        varnish.service
Source3:        varnishncsa.service
Source4:        varnishlog.service
Source5:	varnish.logrotate
Source6:	default.vcl
Patch0:		varnish.varnishtest_debugflag.patch
Patch1:		varnish-3.0.3-link.patch
Patch2:		varnish-3.0.3-automake-1.13.patch
Patch3:		varnish-3.0.3-CVE-2013-4484.patch
BuildRequires:	ncurses-devel
BuildRequires:	libxslt-proc
BuildRequires:	pcre-devel
BuildRequires:	groff
# Varnish actually needs gcc installed to work. It uses the C compiler 
# at runtime to compile the VCL configuration files. This is by design.
Requires:	gcc
Requires(post): systemd
Requires(post): util-linux

%description
This is the Varnish high-performance HTTP accelerator. Documentation wiki and
additional information about Varnish is available on the following web site:
http://www.varnish-cache.org/

%package -n	%{libname}
Summary:	Shared libraries for varnish
Group:		System/Libraries

%description -n	%{libname}
Varnish is a high-performance HTTP accelerator.

This package provides the shared libraries for varnish.

%package -n	%{develname}
Summary:	Development headers and libraries for varnish
Group:		Development/C
Requires:	%{libname} = %{version}
Provides:	%{name}-devel = %{version}-%{release}

%description -n	%{develname}
Varnish is a high-performance HTTP accelerator.

This package provides the development files for varnish.

%prep
%setup -q
%patch0 -p1
%patch1 -p0
%patch2 -p0
%patch3 -p0

# Hack to get 32- and 64-bits tests run concurrently on the same build machine
case `uname -m` in
	ppc64 | s390x | x86_64 | sparc64 )
		sed -i '
			s,9001,9011,g;
			s,9080,9090,g;
			s,9081,9091,g;
			s,9082,9092,g;
			s,9180,9190,g;
		' bin/varnishtest/*.c bin/varnishtest/tests/*vtc
		;;
	*)
		;;
esac

mkdir examples
cp bin/varnishd/default.vcl etc/zope-plone.vcl examples

mkdir -p Mandriva
cp %{SOURCE5} Mandriva/varnish.logrotate
cp %{SOURCE6} Mandriva/default.vcl

%build
autoreconf -fi

%configure2_5x \
    --disable-static \
    --localstatedir=/var/lib

# We have to remove rpath - not allowed in Fedora
# (This problem only visible on 64 bit arches)
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g;
	s|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%make

%install

%makeinstall_std INSTALL="install -p"

install -d %{buildroot}%{_sysconfdir}/varnish
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}/var/lib/varnish
install -d %{buildroot}/var/log/varnish

mkdir -p %{buildroot}%{_unitdir}
install -D -m 0644 %SOURCE1 %{buildroot}%{_unitdir}/varnish.service
install -D -m 0644 %SOURCE3 %{buildroot}%{_unitdir}/varnishncsa.service
install -D -m 0644 %SOURCE4 %{buildroot}%{_unitdir}/varnishlog.service
install -m0644 Mandriva/varnish.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/varnish
install -m0644 Mandriva/default.vcl %{buildroot}%{_sysconfdir}/varnish/default.vcl

# cleanup
find %{buildroot}/%{_libdir}/ -name '*.la' -exec rm -f {} ';'

mkdir -p %{buildroot}%{_tmpfilesdir}
cat <<EOF > %{buildroot}%{_tmpfilesdir}/%{name}.conf
d /run/varnish 0755 varnish varnish
EOF

# Use the new ld.so.conf.d
mkdir -p %{buildroot}/%{_sysconfdir}/ld.so.conf.d
pushd %{buildroot}/%{_sysconfdir}/ld.so.conf.d
echo "%{_libdir}/varnish" > %{name}.conf
popd

%pre
getent group varnish >/dev/null || groupadd -r varnish
getent passwd varnish >/dev/null || \
	useradd -r -g varnish -d /var/lib/varnish -s /sbin/nologin \
		-c "Varnish http accelerator user" varnish
exit 0

%post
if [ ! -f %{_sysconfdir}/%{name}/secret ]; then
	uuidgen > %{_sysconfdir}/%{name}/secret
	chown %{name}:adm %{_sysconfdir}/%{name}/secret
	chmod 0660 %{_sysconfdir}/%{name}/secret

	# While not strictly related, we also need to fix storage permissions from
	# older versions and the lack of a secret file is a good indicator
	find /var/lib/%{name}/ -uid 0 -exec chown %{name}:%{name} {} \;
fi
%_tmpfilescreate %{name}
%_post_service %{name} %{name} varnishlog varnishncsa

%preun
%_preun_service %{name} %{name} varnishlog varnishncsa

%files
%doc INSTALL README ChangeLog examples
%config(noreplace) %{_sysconfdir}/logrotate.d/varnish
%dir %{_sysconfdir}/varnish
%config(noreplace) %{_sysconfdir}/varnish/default.vcl
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/*
%{_unitdir}/varnish.service
%{_unitdir}/varnishncsa.service
%{_unitdir}/varnishlog.service
%{_tmpfilesdir}/%{name}.conf
%{_sbindir}/*
%{_bindir}/*
%attr(0755,varnish,varnish) %dir /var/lib/varnish
%attr(0755,varnish,varnish) %dir /var/log/varnish
%{_mandir}/man1/*.1*
%{_mandir}/man7/*.7*
%dir %{_libdir}/varnish
%{_libdir}/varnish/libvarnish.so
%{_libdir}/varnish/libvarnishcompat.so
%{_libdir}/varnish/libvcl.so
%{_libdir}/varnish/libvgz.so
%dir %{_libdir}/varnish/vmods
%{_libdir}/varnish/vmods/libvmod_std.so
%{_mandir}/man3/vmod_std.3*

%files -n %{libname}
%doc LICENSE
%{_libdir}/lib*.so.%{major}*

%files -n %{develname}
%{_libdir}/lib*.so
%dir %{_includedir}/varnish
%{_includedir}/varnish/*.h
%{_libdir}/pkgconfig/*.pc

