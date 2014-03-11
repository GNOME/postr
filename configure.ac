AC_PREREQ([2.67])

AC_INIT([Postr],[0.20],[https://bugzilla.gnome.org/browse.cgi?product=postr],[postr],[https://wiki.gnome.org/Apps/Postr])
AC_CONFIG_SRCDIR([src/postr.py])
AM_INIT_AUTOMAKE([1.11.1])

AC_CONFIG_MACRO_DIR([m4])

AM_PATH_PYTHON
PKG_CHECK_MODULES(POSTR,
		  pygobject-3.0
		  libnautilus-extension >= 3.0)

AC_ARG_WITH(nautilus-extension-dir,
	    [AS_HELP_STRING([--with-nautilus-extension-dir],
		    [specify the nautilus extension directory])])

AC_MSG_CHECKING([for nautilus extension directory])
if test -n "$with_nautilus_extension_dir"; then
    NAUTILUS_EXTENSION_DIR=$with_nautilus_extension_dir
else
dnl nautilus-python provides the pythondir variable, however its
dnl path is absolute and the prefix can not be overrided (aarrgh!).
dnl So, we have to use a workaround.
  test "x$prefix" != "xNONE" && NAUTILUS_EXTENSION_DIR=`$PKG_CONFIG --variable=pythondir nautilus-python | sed -n -e 's,/$,,' -e '/.*\/lib\/nautilus\/.*\/python$/{s,.*/\(lib/nautilus/.*/python\)$,\1,;p;q;}'`
  NAUTILUS_EXTENSION_DIR=[$prefix/$NAUTILUS_EXTENSION_DIR]
fi
AC_SUBST([nautilusextensiondir], [$NAUTILUS_EXTENSION_DIR])

dnl i10n support / gettext
IT_PROG_INTLTOOL([0.40.0])
GETTEXT_PACKAGE="postr"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])

GNOME_DOC_INIT

AC_CONFIG_FILES([
Makefile
po/Makefile.in
data/postr.desktop.in
help/Makefile
])
AC_OUTPUT

echo $PACKAGE......... : $VERSION
echo Prefix........... : $prefix
echo Nautilus Python.. : $nautilusextensiondir
