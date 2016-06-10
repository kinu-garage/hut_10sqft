; .emacs specific for Ubuntu Trusty

(load "~/link/github_repos/130s/compenv_ubuntu/config/emacs/emacs_ubuntu.el")

; 3/5/2015 for ibus
(require 'ibus)
(add-hook 'after-init-hook 'ibus-mode-on)
(add-hook 'after-init-hook 'ibus-mode)

;; Custom ROS location
(set-register ?r '(file . "~/link/ROS/indigo_trusty/"))
