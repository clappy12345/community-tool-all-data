"""Keyboard shortcuts — injected once per page via a zero-height component.

Shortcuts:
    N       Next page (sidebar nav)
    P       Previous page
    /       Focus the message search input
    ?       Toggle keyboard shortcuts help overlay
    Esc     Close the help overlay
"""
from __future__ import annotations

import streamlit.components.v1 as components

_JS = """<script>
(function(){
    var doc = window.parent.document;
    if (doc._kbBound) return;
    doc._kbBound = true;

    if (!doc.getElementById('kb-help-overlay')) {
        var d = doc.createElement('div');
        d.id = 'kb-help-overlay';
        d.style.cssText = 'position:fixed;inset:0;z-index:999999;background:rgba(0,0,0,0.55);'
            + 'display:none;align-items:center;justify-content:center;'
            + 'backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);';
        d.addEventListener('click', function(){ d.style.display='none'; });

        var card = doc.createElement('div');
        card.style.cssText = 'background:#1A1D23;border:1px solid rgba(0,180,216,0.2);'
            + 'border-radius:14px;padding:28px 34px;max-width:400px;width:92%;'
            + 'box-shadow:0 12px 40px rgba(0,0,0,0.5);';
        card.addEventListener('click', function(e){ e.stopPropagation(); });

        var kbdStyle = 'background:rgba(0,180,216,0.15);color:#00B4D8;padding:3px 10px;'
            + 'border-radius:6px;font-size:0.82rem;font-weight:700;font-family:inherit;';

        card.innerHTML = ''
            + '<div style="font-size:1.15rem;font-weight:800;color:#FAFAFA;margin-bottom:20px;">'
            + '\\u2328\\uFE0F Keyboard Shortcuts</div>'
            + '<table style="width:100%;border-collapse:collapse;">'
            + '<tr><td style="padding:8px 0;color:#8899A6;font-size:0.88rem;">Next page</td>'
            + '<td style="text-align:right;"><kbd style="' + kbdStyle + '">N</kbd></td></tr>'
            + '<tr><td style="padding:8px 0;color:#8899A6;font-size:0.88rem;">Previous page</td>'
            + '<td style="text-align:right;"><kbd style="' + kbdStyle + '">P</kbd></td></tr>'
            + '<tr><td style="padding:8px 0;color:#8899A6;font-size:0.88rem;">Focus search</td>'
            + '<td style="text-align:right;"><kbd style="' + kbdStyle + '">/</kbd></td></tr>'
            + '<tr><td style="padding:8px 0;color:#8899A6;font-size:0.88rem;">Show shortcuts</td>'
            + '<td style="text-align:right;"><kbd style="' + kbdStyle + '">?</kbd></td></tr>'
            + '</table>'
            + '<div style="text-align:center;margin-top:18px;font-size:0.72rem;color:#8899A6;">'
            + 'Press <kbd style="' + kbdStyle + '">Esc</kbd> or click outside to close</div>';

        d.appendChild(card);
        doc.body.appendChild(d);
    }

    doc.addEventListener('keydown', function(e) {
        var tag = (e.target.tagName || '').toLowerCase();
        var editing = tag === 'input' || tag === 'textarea' || tag === 'select'
                      || e.target.isContentEditable;

        if (e.key === 'Escape') {
            var h = doc.getElementById('kb-help-overlay');
            if (h) h.style.display = 'none';
            return;
        }

        if (editing) return;

        if (e.key === '?') {
            var h = doc.getElementById('kb-help-overlay');
            if (h) {
                h.style.display = h.style.display === 'none' ? 'flex' : 'none';
                e.preventDefault();
            }
            return;
        }

        var links = Array.from(
            doc.querySelectorAll('[data-testid="stSidebarNavItems"] a')
        );
        if (!links.length) {
            links = Array.from(
                doc.querySelectorAll('nav[data-testid="stSidebarNav"] a')
            );
        }
        if (!links.length) return;

        var path = window.parent.location.pathname.replace(/\\/+$/, '');
        var idx = -1;
        for (var i = 0; i < links.length; i++) {
            if (links[i].pathname.replace(/\\/+$/, '') === path) { idx = i; break; }
        }
        if (idx === -1) idx = 0;

        if (e.key === 'n') {
            if (idx < links.length - 1) { links[idx + 1].click(); e.preventDefault(); }
        } else if (e.key === 'p') {
            if (idx > 0) { links[idx - 1].click(); e.preventDefault(); }
        } else if (e.key === '/') {
            var s = doc.querySelector(
                'input[placeholder*="keyword"], input[placeholder*="Search"], '
                + 'input[placeholder*="search"]'
            );
            if (s) { s.focus(); s.select(); e.preventDefault(); }
        }
    });
})();
</script>"""


def inject_keyboard_shortcuts():
    """Call once per page (via apply_theme) to enable keyboard navigation."""
    components.html(_JS, height=0, scrolling=False)
