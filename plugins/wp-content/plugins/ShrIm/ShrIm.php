<?php
/*
Plugin Name: Shr.im
Plugin URI: http://shr.im/tools/
Description: Convertit automatiquement les liens externes de vos articles en lien shr.im
Version: 1.0.0
Author: Jordane VASPARD
Author URI: http://jordane.vaspard.fr/
*/

/*  
  OBLIGATOIRE, licence
*/

/*
  J'ai fais des fonctions parce que c'est le plus simple et le plus rapide pour expérimenter, l'idéal, c'est d'encapsuler tout ça dans une classe.
	J'ai pas commenté non plus encore.
*/

	function ShrImInstall() {
	
	}
	
	function ShrImUninstall() {
	
	}
	
	function ShrImAddLinkMenu() {
    add_options_page('Shr.im Options', 'Extension Shr.im', 8, __FILE__, 'ShrImDisplayForm');
	}
	
	function ShrImDisplayForm() {
    echo '<div class="wrap"><h2>Options de l\'extension Shr.im</h2><form method="post" action="options.php">';
    wp_nonce_field('update-options');
		echo '<table class="form-table"><tr valign="top"><th scope="row">Nom d\'utilisateur</th><td><input type="text" name="shrim_username" value="'.get_option('shrim_username').'" /></td></tr><tr valign="top"><th scope="row">Clé API</th><td><input type="text" name="shrim_apikey" value="'.get_option('shrim_apikey').'" /></td></tr></table><input type="hidden" name="action" value="update" /><input type="hidden" name="page_options" value="shrim_username,shrim_apikey" /><p class="submit"><input type="submit" class="button-primary" value="';
		_e('Save Changes');
		echo '" /></p></form></div>';
	}
	
	function ShrImApply($pPostID) {
	  echo 'Le post '.$pPostID.' doit être parsé.';
		// requete sql pour update
		exit;
	}

// ~ Définition de la méthode à appeller lors de l'installation du plugin.
  register_activation_hook(__FILE__, ShrImInstall());

// ~ Définition de la méthode à appeller lors de la désinstallation du plugin.	
  register_deactivation_hook(__FILE__, ShrImUninstall());

// ~ Définition de la méthode à appeller pour ajouter un menu dans Wordpress
  add_action('admin_menu', 'ShrImAddLinkMenu');
	
// ~ Définition de la méthode à chaque fois qu'un post a été créé ou édité	
	add_filter('save_post', 'ShrImApply', 1, 1);


?>