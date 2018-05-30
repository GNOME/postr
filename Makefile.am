ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}

SUBDIRS = help po

bin_SCRIPTS = postr

uidir = $(datadir)/postr
ui_DATA = src/postr.glade

postrdir = $(pythondir)/postr

postr_PYTHON = \
	src/AboutDialog.py \
	src/AuthenticationDialog.py \
	src/ContentTypeCombo.py \
	src/DummyUnique.py \
	src/EXIF.py \
	src/ErrorDialog.py \
	src/GroupSelector.py \
	src/ImageList.py \
	src/ImageStore.py \
	src/LicenseCombo.py \
	src/PrivacyCombo.py \
	src/ProgressDialog.py \
	src/PyUnique.py \
	src/SafetyCombo.py \
	src/SetCombo.py \
	src/StatusBar.py \
	src/TagsEntry.py \
	src/__init__.py \
	src/flickrest.py \
	src/iptcinfo.py \
	src/postr.py \
	src/proxyclient.py \
	src/util.py \
	src/version.py

# Nautilus extension
postrnautilusdir = $(nautilusextensiondir)/
postrnautilus_PYTHON = nautilus/postrExtension.py

# icons
iconthemedir = $(datadir)/icons/hicolor
appicon16dir = $(iconthemedir)/16x16/apps
appicon22dir = $(iconthemedir)/22x22/apps
appicon24dir = $(iconthemedir)/24x24/apps
appicon32dir = $(iconthemedir)/32x32/apps
appicon32dir = $(iconthemedir)/48x48/apps
appicon32dir = $(iconthemedir)/256x256/apps
appiconscdir = $(iconthemedir)/scalable/apps

dist_appicon16_DATA = data/16x16/postr.png
dist_appicon22_DATA = data/22x22/postr.png
dist_appicon24_DATA = data/24x24/postr.png
dist_appicon32_DATA = data/32x32/postr.png
dist_appicon32_DATA = data/48x48/postr.png
dist_appicon32_DATA = data/256x256/postr.png
dist_appiconsc_DATA = data/scalable/postr.svg

noinst_icons = data/16x16/postr.svg \
	data/22x22/postr.svg \
	data/32x32/postr.svg

dist_noinst_DATA = $(noinst_icons)

# desktop file & translation
@INTLTOOL_DESKTOP_RULE@
desktopdir = $(datadir)/applications
desktop_in_in_files = data/postr.desktop.in.in
desktop_in_files = $(desktop_in_in_files:.desktop.in.in=.desktop.in)
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

DISTCHECK_CONFIGURE_FLAGS = --disable-scrollkeeper

dist_noinst_SCRIPTS = autogen.sh

EXTRA_DIST = \
	$(bin_SCRIPTS) \
	$(ui_DATA) \
	$(desktop_in_in_files) \
	gnome-doc-utils.make

CLEANFILES = $(desktop_DATA)

DISTCLEANFILES = \
	$(desktop_in_files) \
	intltool-extract \
	intltool-merge \
	intltool-update \
	$(srcdir)/po/Rules-quot \
	$(srcdir)/po/Makevars.template \
	$(srcdir)/po/*.sin \
	$(srcdir)/po/*.sed \
	$(srcdir)/po/en@*.header \
	ChangeLog

# MAINTAINERCLEANFILES is ad-hoc and it does not follow the
# heuristic recommended in the documentation.  It is used to
# clean as much as possible the directory to leave as close
# to the repository.  So, you are warned if you would like
# to use it as template for your own Makefile's rules.
MAINTAINERCLEANFILES = \
	$(dist_docutils) $(dist_intltool) \
	$(srcdir)/ABOUT-NLS \
	$(srcdir)/INSTALL \
	$(srcdir)/gnome-doc-utils.make \
	$(srcdir)/Makefile.in \
	$(srcdir)/aclocal.m4 \
	$(srcdir)/config.h.in \
	$(srcdir)/install-sh \
	$(srcdir)/missing \
	$(srcdir)/mkinstalldirs \
	$(srcdir)/py-compile \
	$(srcdir)/config.rpath \
	$(srcdir)/config.sub \
	$(srcdir)/config.rpath \
	$(srcdir)/config.guess \
	$(srcdir)/configure

maintainer-clean-local: maintainer-clean-local-check
# We are tough! (or just stupid)
maintainer-clean-local-check:
	rm -rf m4
	rm -f po/Makefile.*~

ChangeLog:
	@echo Creating $@
	@if test -d "$(srcdir)/.git"; then \
	  (GIT_DIR=$(top_srcdir)/.git ./missing --run git log --stat -M -C --name-status  --date=short --no-color) | fmt --split-only > $@.tmp \
	  && mv -f $@.tmp $@ \
	  || ($(RM) $@.tmp; \
	      echo Failed to generate ChangeLog, your ChangeLog may be outdated >&2; \
	      (test -f $@ || echo git-log is required to generate this file >> $@)); \
	else \
	  test -f $@ || \
	  (echo A git checkout and git-log is required to generate ChangeLog >&2 && \
	   echo A git checkout and git-log is required to generate this file >> $@); \
	fi

gtk_update_icon_cache = gtk-update-icon-cache -f -t $(datadir)/icons/hicolor

install-data-hook: update-icon-cache
uninstall-hook: update-icon-cache
update-icon-cache:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating Gtk icon cache."; \
		$(gtk_update_icon_cache); \
	else \
		echo "*** Icon cache not updated.  After (un)install, run this:"; \
		echo "***   $(gtk_update_icon_cache)"; \
	fi

.PHONY: ChangeLog maintainer-clean-local-check
