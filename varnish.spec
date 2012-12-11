%define _disable_ld_as_needed 1
%define _disable_ld_no_undefined 1

%define major 1
%define libname %mklibname varnish %{major}
%define develname %mklibname varnish -d

Summary:	Varnish is a high-performance HTTP accelerator
Name:		varnish
Version:	3.0.3
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


%changelog
* Sat Feb 11 2012 Oden Eriksson <oeriksson@mandriva.com> 3.0.2-2mdv2012.0
+ Revision: 773084
- relink against libpcre.so.1

* Sun Nov 06 2011 Alexander Khrukin <akhrukin@mandriva.org> 3.0.2-1
+ Revision: 721585
- version update to upstream

* Wed Jun 29 2011 Oden Eriksson <oeriksson@mandriva.com> 3.0.0-1
+ Revision: 688191
- 3.0.0

* Sun Feb 06 2011 Oden Eriksson <oeriksson@mandriva.com> 2.1.5-1
+ Revision: 636367
- 2.1.5

* Tue Nov 09 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1.4-1mdv2011.0
+ Revision: 595425
- 2.1.4

* Mon Aug 09 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1.3-1mdv2011.0
+ Revision: 568102
- 2.1.3

* Thu Mar 25 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1-1mdv2010.1
+ Revision: 527360
- fix deps
- 2.1
- rediffed one patch

* Mon Dec 28 2009 Oden Eriksson <oeriksson@mandriva.com> 2.0.6-1mdv2010.1
+ Revision: 482989
- 2.0.6

* Thu Nov 12 2009 Oden Eriksson <oeriksson@mandriva.com> 2.0.5-1mdv2010.1
+ Revision: 465385
- 2.0.5

* Mon May 18 2009 Oden Eriksson <oeriksson@mandriva.com> 2.0.4-1mdv2010.0
+ Revision: 377188
- 2.0.4

* Sat Feb 14 2009 Oden Eriksson <oeriksson@mandriva.com> 2.0.3-1mdv2009.1
+ Revision: 340321
- 2.0.3

* Mon Dec 01 2008 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-1mdv2009.1
+ Revision: 308756
- import varnish


* Mon Dec 01 2008 Oden Eriksson <oeriksson@mandriva.com> 2.0.2-1mdv2009.0
- initial Mandriva package (fedora import)
- use both _disable_ld_as_needed and _disable_ld_no_undefined
  due to extremely ugly autopoo

* Mon Nov 10 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0.2-1
  New upstream release 2.0.2. A bugfix release

* Sun Nov 02 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0.1-2
- Removed the requirement for kernel => 2.6.0. All supported
  platforms meets this, and it generates strange errors in EPEL

* Fri Oct 17 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0.1-1
- 2.0.1 released, a bugfix release. New upstream sources
- Package now also available in EPEL

* Thu Oct 16 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-2
- Readded the debugflag patch. It's so practical
- Added a strange workaround for make check on ppc64

* Wed Oct 15 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-1
- 2.0 released. New upstream sources
- Disabled jemalloc on ppc and ppc64. Added a note in README.redhat
- Synced to upstream again. No more patches needed

* Wed Oct 08 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.11.rc1
- 2.0-rc1 released. New upstream sources
- Added a patch for pagesize to match redhat's rhel5 ppc64 koji build boxes
- Added a patch for test a00008, from r3269
- Removed condrestart in postscript at upgrade. We don't want that

* Fri Sep 26 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.10.beta2
- 2.0-beta2 released. New upstream sources
- Whitespace changes to make rpmlint more happy

* Fri Sep 12 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.9.20080912svn3184
- Added varnisnsca init script (Colin Hill)
- Corrected varnishlog init script (Colin Hill)

* Tue Sep 09 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.8.beta1
- Added a patch from r3171 that fixes an endian bug on ppc and ppc64
- Added a hack that changes the varnishtest ports for 64bits builds,
  so they can run in parallell with 32bits build on same build host

* Tue Sep 02 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.7.beta1
- Added a patch from r3156 and r3157, hiding a legit errno in make check

* Tue Sep 02 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.6.beta1
- Added a commented option for max coresize in the sysconfig script
- Added a comment in README.redhat about upgrading from 1.x to 2.0

* Fri Aug 29 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.5.beta1
- Bumped version numbers and source url for first beta release \o/
- Added a missing directory to the libs-devel package (Michael Schwendt)
- Added the LICENSE file to the libs-devel package
- Moved make check to its proper place
- Removed superfluous definition of lockfile in initscripts

* Wed Aug 27 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.4.20080827svn3136
- Fixed up init script for varnishlog too

* Mon Aug 25 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.3.20080825svn3125
- Fixing up init script according to newer Fedora standards
- The build now runs the test suite after compiling
- Requires initscripts
- Change default.vcl from nothing but comments to point to localhost:80,

* Mon Aug 18 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.2.tp2
- Changed source, version and release to match 2.0-tp2

* Thu Aug 14 2008 Ingvar Hagelund <ingvar@linpro.no> - 2.0-0.1.20080814svn
- default.vcl has moved
- Added groff to build requirements

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1.1.2-6
- Autorebuild for GCC 4.3

* Sat Dec 29 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.2-5
- Added missing configuration examples
- Corrected the license to "BSD"

* Fri Dec 28 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.2-4
- Build for fedora update

* Fri Dec 28 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.2-2
- Added missing changelog items

* Thu Dec 20 2007 Stig Sandbeck Mathisen <ssm@linpro.no> - 1.1.2-1
- Bumped the version number to 1.1.2.
- Addeed build dependency on libxslt

* Wed Sep 08 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.1-3
- Added a patch, changeset 1913 from svn trunk. This makes varnish
  more stable under specific loads. 

* Tue Sep 06 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.1-2
- Removed autogen call (only diff from relase tarball)

* Mon Aug 20 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.1-1
- Bumped the version number to 1.1.1.

* Tue Aug 14 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.1.svn
- Update for 1.1 branch
- Added the devel package for the header files and static library files
- Added a varnish user, and fixed the init script accordingly

* Thu Jul 05 2007 Dag-Erling Smørgrav <des@des.no> - 1.1-1
- Bump Version and Release for 1.1

* Mon May 28 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.4-3
- Fixed initrc-script bug only visible on el4 (fixes #107)

* Sun May 20 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.4-2
- Repack from unchanged 1.0.4 tarball
- Final review request and CVS request for Fedora Extras
- Repack with extra obsoletes for upgrading from older sf.net package

* Fri May 18 2007 Dag-Erling Smørgrav <des@des.no> - 1.0.4-1
- Bump Version and Release for 1.0.4

* Wed May 16 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.svn-20070517
- Wrapping up for 1.0.4
- Changes in sysconfig and init scripts. Syncing with files in
  trunk/debian

* Fri May 11 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.svn-20070511
- Threw latest changes into svn trunk
- Removed the conversion of manpages into utf8. They are all utf8 in trunk

* Wed May 09 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-7
- Simplified the references to the subpackage names
- Added init and logrotate scripts for varnishlog

* Mon Apr 23 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-6
- Removed unnecessary macro lib_name
- Fixed inconsistently use of brackets in macros
- Added a condrestart to the initscript
- All manfiles included, not just the compressed ones
- Removed explicit requirement for ncurses. rpmbuild figures out the 
  correct deps by itself.
- Added ulimit value to initskript and sysconfig file
- Many thanks to Matthias Saou for valuable input

* Mon Apr 16 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-5
- Added the dist tag
- Exchanged  RPM_BUILD_ROOT variable for buildroot macro
- Removed stripping of binaries to create a meaningful debug package
- Removed BuildRoot and URL from subpackages, they are picked from the
  main package
- Removed duplication of documentation files in the subpackages
- 'chkconfig --list' removed from post script
- Package now includes _sysconfdir/varnish/
- Trimmed package information
- Removed static libs and .so-symlinks. They can be added to a -devel package
  later if anybody misses them

* Wed Feb 28 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-4
- More small specfile fixes for Fedora Extras Package
  Review Request, see bugzilla ticket 230275
- Removed rpath (only visible on x86_64 and probably ppc64)

* Tue Feb 27 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-3
- Made post-1.0.3 changes into a patch to the upstream tarball
- First Fedora Extras Package Review Request

* Fri Feb 23 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-2
- A few other small changes to make rpmlint happy

* Thu Feb 22 2007 Ingvar Hagelund <ingvar@linpro.no> - 1.0.3-1
- New release 1.0.3. See the general ChangeLog
- Splitted the package into varnish, libvarnish1 and
  libvarnish1-devel

* Thu Oct 19 2006 Ingvar Hagelund <ingvar@linpro.no> - 1.0.2-7
- Added a Vendor tag

* Thu Oct 19 2006 Ingvar Hagelund <ingvar@linpro.no> - 1.0.2-6
- Added redhat subdir to svn
- Removed default vcl config file. Used the new upstream variant instead.
- Based build on svn. Running autogen.sh as start of build. Also added
  libtool, autoconf and automake to BuildRequires.
- Removed rule to move varnishd to sbin. This is now fixed in upstream
- Changed the sysconfig script to include a lot more nice features.
  Most of these were ripped from the Debian package. Updated initscript
  to reflect this.

* Tue Oct 10 2006 Ingvar Hagelund <ingvar@linpro.no> - 1.0.1-3
- Moved Red Hat specific files to its own subdirectory

* Tue Sep 26 2006 Ingvar Hagelund <ingvar@linpro.no> - 1.0.1-2
- Added gcc requirement.
- Changed to an even simpler example vcl in to /etc/varnish (thanks, perbu)
- Added a sysconfig entry

* Fri Sep 22 2006 Ingvar Hagelund <ingvar@linpro.no> - 1.0.1-1
- Initial build.












