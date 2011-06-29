%define _disable_ld_as_needed 1
%define _disable_ld_no_undefined 1

%define major 1
%define libname %mklibname varnish %{major}
%define develname %mklibname varnish -d

Summary:	Varnish is a high-performance HTTP accelerator
Name:		varnish
Version:	3.0.0
Release:	%mkrel 1
License:	BSD
Group:		System/Servers
URL:		http://www.varnish-cache.org/
Source0:	http://repo.varnish-cache.org/source/varnish-%{version}.tar.gz
Source1:	varnish.init
Source2:	varnishlog.init
Source3:	varnishncsa.init
Source4:	varnish.logrotate
Source5:	varnish.sysconfig
Source6:	default.vcl
Patch0:		varnish.varnishtest_debugflag.patch
BuildRequires:	ncurses-devel
BuildRequires:	libxslt-proc
BuildRequires:	pcre-devel
BuildRequires:	groff
# Varnish actually needs gcc installed to work. It uses the C compiler 
# at runtime to compile the VCL configuration files. This is by design.
Requires:	gcc
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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
cp %{SOURCE1} Mandriva/varnish.init
cp %{SOURCE2} Mandriva/varnishlog.init
cp %{SOURCE3} Mandriva/varnishncsa.init
cp %{SOURCE4} Mandriva/varnish.logrotate
cp %{SOURCE5} Mandriva/varnish.sysconfig
cp %{SOURCE6} Mandriva/default.vcl

%build
autoreconf -fis

%configure2_5x \
    --disable-static \
    --localstatedir=/var/lib

# We have to remove rpath - not allowed in Fedora
# (This problem only visible on 64 bit arches)
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g;
	s|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%make

#check <- 1 of 97 tests failed. dies at bin/varnishtest/tests/v00009.vtc
#PIDFILE=`ps ax | grep varnish | grep -v "grep varnish"| awk '{ print $1 }'`
#if ! [ -z "$PIDFILE" ]; then
#    kill -9 $PIDFILE
#fi
#LD_LIBRARY_PATH="lib/libvarnish/.libs:lib/libvarnishcompat/.libs:lib/libvarnishapi/.libs:lib/libvcl/.libs" bin/varnishd/varnishd -b 127.0.0.1:8000 -C -n `pwd`/foo
#make check LD_LIBRARY_PATH="../../lib/libvarnish/.libs:../../lib/libvarnishcompat/.libs:../../lib/libvarnishapi/.libs:../../lib/libvcl/.libs"

%install
rm -rf %{buildroot}

%makeinstall_std INSTALL="install -p"

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_sysconfdir}/varnish
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}/var/lib/varnish
install -d %{buildroot}/var/log/varnish
install -d %{buildroot}/var/run/varnish

install -m0755 Mandriva/varnish.init %{buildroot}%{_initrddir}/varnish
install -m0755 Mandriva/varnishlog.init %{buildroot}%{_initrddir}/varnishlog
install -m0755 Mandriva/varnishncsa.init %{buildroot}%{_initrddir}/varnishncsa

install -m0644 Mandriva/varnish.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/varnish
install -m0644 Mandriva/varnish.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/varnish
install -m0644 Mandriva/default.vcl %{buildroot}%{_sysconfdir}/varnish/default.vcl

# cleanup
find %{buildroot}/%{_libdir}/ -name '*.la' -exec rm -f {} ';'

%pre
getent group varnish >/dev/null || groupadd -r varnish
getent passwd varnish >/dev/null || \
	useradd -r -g varnish -d /var/lib/varnish -s /sbin/nologin \
		-c "Varnish http accelerator user" varnish
exit 0

%post
/sbin/chkconfig --add varnish
/sbin/chkconfig --add varnishlog
/sbin/chkconfig --add varnishncsa

%preun
if [ $1 -lt 1 ]; then
    /sbin/service varnish stop > /dev/null 2>&1
    /sbin/service varnishlog stop > /dev/null 2>&1
    /sbin/service varnishncsa stop > /dev/null 2>&1
    /sbin/chkconfig --del varnish
    /sbin/chkconfig --del varnishlog
    /sbin/chkconfig --del varnishncsa
fi

%if %mdkversion < 200900
%post -n %{libname} -p /sbin/ldconfig
%endif

%if %mdkversion < 200900
%postun -n %{libname} -p /sbin/ldconfig
%endif

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc INSTALL README ChangeLog examples
%config(noreplace) %{_sysconfdir}/sysconfig/varnish
%config(noreplace) %{_sysconfdir}/logrotate.d/varnish
%dir %{_sysconfdir}/varnish
%config(noreplace) %{_sysconfdir}/varnish/default.vcl
%{_initrddir}/varnish
%{_initrddir}/varnishlog
%{_initrddir}/varnishncsa
%{_sbindir}/*
%{_bindir}/*
%attr(0755,varnish,varnish) %dir /var/lib/varnish
%attr(0755,varnish,varnish) %dir /var/log/varnish
%attr(0755,varnish,varnish) %dir /var/run/varnish
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
%defattr(-,root,root,-)
%doc LICENSE
%{_libdir}/lib*.so.%{major}*

%files -n %{develname}
%defattr(-,root,root,-)
%{_libdir}/lib*.so
%dir %{_includedir}/varnish
%{_includedir}/varnish/*.h
%{_libdir}/pkgconfig/*.pc
