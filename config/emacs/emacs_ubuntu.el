;; 9/16/2011 For Mozc + ibus
;; Turn on ibus-mode automatically after loading .emacs
(require 'ibus)  ;; This requires ibus-el to be installed (available via apt)
(add-hook 'after-init-hook 'ibus-mode-on)
;; Use C-SPC for Set Mark command
(ibus-define-common-key ?\C-\s nil)
;; Use C-/ for Undo command
;(ibus-define-common-key ?\C-/ nil)
;; Change cursor color depending on IBus status
(setq ibus-cursor-color '("limegreen" "white" "blue"))
(global-set-key "\C-\o" 'ibus-toggle)

; 6/30/2012/http://superuser.com/questions/165278/copying-text-from-emacs-into-other-programs
(setq x-select-enable-clipboard t)      ;Make kill/yank work with the X clipboard
(setq interprogram-paste-function 'x-cut-buffer-or-selection-value)

; 2/15/2016 Without this, encoding may not be saved proerply?
(set-language-environment "Japanese")
