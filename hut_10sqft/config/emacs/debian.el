; .emacs specific for Debian OS
; 20240125 Originally copied from emacs_chromeos.el
; One example of Debian entity is Linux mode on ChromeOS, where paths are inevitably different from other Ubuntu hosts.

(load "~/.config/hut_10sqft/hut_10sqft/config/emacs/emacs.el")

;; Toggling OS language choice
;;
;; The following, which is taken from an Emacs config on Linux, doesn't seem to work (likely because `toggle-input-method` doesn't work on ChromeOS?).
; (global-set-key (kbd "\C-q") 'toggle-input-method)

;;20240117 Copied from ./emacs_ubuntu.el and modified hoping this works on ChromeOS. See https://github.com/kinu-garage/hut_10sqft/issues/983
;; mozc
(require 'mozc)
; 2/15/2016 Without this, encoding may not be saved proerply?
(set-language-environment "Japanese")
(setq default-input-method "japanese-mozc")
;;;(global-set-key (kbd "\C-o") 'toggle-input-method)  ; This doesn't seem to be working. Probably collides with OS' input key that is also \C-o ?
(global-set-key (kbd "\C-q") 'toggle-input-method)
; 20160609 Not sure how effective this is but I just leave it. https://wiki.archlinuxjp.org/index.php/Mozc#Emacs_.E3.81.A7_Mozc_.E3.82.92.E4.BD.BF.E3.81.86
(setq mozc-candidate-style 'overlay)
