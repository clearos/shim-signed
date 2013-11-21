Name:           shim-signed
Version:        0.7
Release:        5%{?dist}
Summary:        First-stage UEFI bootloader
Provides:	shim = %{version}-%{release}
%define unsigned_release 4%{?dist}

License:        BSD
URL:            http://www.codon.org.uk/~mjg59/shim/
Source1:	BOOT.CSV
Source2:	redhatsecureboot003.cer
Source3:	redhatsecurebootca2.cer

BuildRequires: shim-unsigned = %{version}-%{unsigned_release}
BuildRequires: pesign >= 0.106-5%{dist}

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
Provides: bundled(openssl) = 0.9.8w

# Shim is only required on platforms implementing the UEFI secure boot
# protocol. The only one of those we currently wish to support is 64-bit x86.
# Adding further platforms will require adding appropriate relocation code.
ExclusiveArch: x86_64

%global debug_package %{nil}

# Figure out the right file path to use
%if 0%{?rhel}
%global efidir redhat
%endif
%if 0%{?fedora}
%global efidir fedora
%endif

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%package -n shim
Summary: First-stage UEFI bootloader
Requires: shim-unsigned = %{version}-%{unsigned_release}
Requires: mokutil = %{version}-%{unsigned_release}
Provides: shim-signed = %{version}-%{release}
Obsoletes: shim-signed < %{version}-%{release}

%description -n shim
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%prep
cd %{_builddir}
rm -rf shim-signed-%{version}
mkdir shim-signed-%{version}

%build
%define vendor_token_str %{expand:%%{nil}%%{?vendor_token_name:-t "%{vendor_token_name}"}}
%define vendor_cert_str %{expand:%%{!?vendor_cert_nickname:-c "Red Hat Test Certificate"}%%{?vendor_cert_nickname:-c "%%{vendor_cert_nickname}"}}

cd shim-signed-%{version}
pesign -i %{_datadir}/shim/shim.efi -h -P > shim.hash
if ! cmp shim.hash %{_datadir}/shim/shim.hash ; then
	echo Invalid signature\! > /dev/stderr
	exit 1
fi
%pesign -s -i %{_datadir}/shim/shim.efi -o shim.efi -a %{SOURCE3} -c %{SOURCE2} -n redhatsecureboot003
%pesign -s -i %{_datadir}/shim/MokManager.efi -o MokManager.efi -a %{SOURCE3} -c %{SOURCE2} -n redhatsecureboot003
%pesign -s -i %{_datadir}/shim/fallback.efi -o fallback.efi -a %{SOURCE3} -c %{SOURCE2} -n redhatsecureboot003

%install
rm -rf $RPM_BUILD_ROOT
cd shim-signed-%{version}
install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
install -m 0644 shim.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim.efi
install -m 0644 MokManager.efi $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/MokManager.efi
install -m 0644 %{SOURCE1} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT.CSV

install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/
install -m 0644 shim.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/BOOTX64.EFI
install -m 0644 fallback.efi $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/fallback.efi

%files -n shim
/boot/efi/EFI/%{efidir}/shim.efi
/boot/efi/EFI/%{efidir}/MokManager.efi
/boot/efi/EFI/%{efidir}/BOOT.CSV
/boot/efi/EFI/BOOT/BOOTX64.EFI
/boot/efi/EFI/BOOT/fallback.efi

%changelog
* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-5
- Fix shim-unsigned deps.
  Related: rhbz#1032583

* Thu Nov 21 2013 Peter Jones <pjones@redhat.com> - 0.7-4
- Make dhcp4 work better.
  Related: rhbz#1032583

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 0.7-3
- Make lockdown include UEFI and other KEK/DB entries.
  Related: rhbz#1030492

* Fri Nov 08 2013 Peter Jones <pjones@redhat.com> - 0.7-2
- Handle SetupMode better in lockdown as well
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.7-1
- Don't treat SetupMode variable's presence as meaning we're in SetupMode.
  Related: rhbz#996863

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 0.6-3
- Use the correct CA and signer certificates.
  Related: rhbz#996863

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 0.6-1
- Update to 0.6-1
  Resolves: rhbz#1008379

* Wed Aug 07 2013 Peter Jones <pjones@redhat.com> - 0.4-3.2
- Depend on newer pesign.
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3.1
- Rebuild with newer pesign
  Related: rhbz#989442

* Tue Aug 06 2013 Peter Jones <pjones@redhat.com> - 0.4-3
- Update for RHEL signing with early test keys.
  Related: rhbz#989442

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 0.4-1
- Provide a fallback for uninitialized Boot#### and BootOrder
  Resolves: rhbz#963359
- Move all signing from shim-unsigned to here
- properly compare our generated hash from shim-unsigned with the hash of
  the signed binary (as opposed to doing it manually)

* Fri May 31 2013 Peter Jones <pjones@redhat.com> - 0.2-4.4
- Re-sign to get alignments that match the new specification.
  Resolves: rhbz#963361

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2-4.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jan 02 2013 Peter Jones <pjones@redhat.com> - 0.2-3.3
- Add obsoletes and provides for earlier shim-signed packages, to cover
  the package update cases where previous versions were installed.
  Related: rhbz#888026

* Mon Dec 17 2012 Peter Jones <pjones@redhat.com> - 0.2-3.2
- Make the shim-unsigned dep be on the subpackage.

* Sun Dec 16 2012 Peter Jones <pjones@redhat.com> - 0.2-3.1
- Rebuild to provide "shim" package directly instead of just as a Provides:

* Sat Dec 15 2012 Peter Jones <pjones@redhat.com> - 0.2-3
- Also provide shim-fedora.efi, signed only by the fedora signer.
- Fix the fedora signature on the result to actually be correct.
- Update for shim-unsigned 0.2-3

* Mon Dec 03 2012 Peter Jones <pjones@redhat.com> - 0.2-2
- Initial build
