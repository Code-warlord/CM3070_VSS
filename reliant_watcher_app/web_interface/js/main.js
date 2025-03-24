// Function to show a specific page and update the URL hash.
function show_page(pageId) {
	// Hide all sections.
	document.querySelectorAll('.page').forEach((page) => page.classList.remove('active'));
	// Show the selected section.
	document.getElementById(pageId).classList.add('active');
	// Update URL hash without reloading the page.
	history.pushState(null, '', `#${pageId}`);
}

// On page load, show the section based on the URL hash or default to "livestream".
window.onload = function () {
	const hash = window.location.hash.substring(1) || 'livestream';
	show_page(hash);
};



// The code below is my own work, written by me for web development (CM1040) coursework,
// it is utilized here to beautify the UI.

// Select the hamburger menu element
const hamburger = document.querySelector('.hamburger');

// Select the navigation element
const nav = document.querySelector('nav');

// Add an event listener to the hamburger menu for click events
hamburger.addEventListener('click', () => {
	// Toggle the 'active' class on the hamburger menu
	hamburger.classList.toggle('active');

	// Update the 'aria-expanded' attribute to reflect the current state
	hamburger.setAttribute('aria-expanded', hamburger.classList.contains('active'));

	// Toggle the 'active' class on the navigation element
	nav.classList.toggle('active');

	// Update the 'aria-hidden' attribute to reflect the current state
	nav.setAttribute('aria-hidden', !nav.classList.contains('active'));
});

// Add an event listener to the hamburger menu for keydown events
hamburger.addEventListener('keydown', (event) => {
	// Check if the Enter key was pressed
	if (event.key === 'Enter') {
		// Simulate a click event on the hamburger menu
		hamburger.click();
	}
});

function change_theme() {
	/**
	 * Changes the theme of the application based on the active theme color.
	 * Its purpose is to adjust various color properties of the page based on a selected theme color, 
	 * ensuring a consistent and visually appealing look across different parts of the site.
	 *
	 * It relies on data stored in the browser's local storage and elements present in the HTML document.
	 *
	 * The main output of this function is the modification of CSS custom properties (variables) that 
	 * control the color scheme of the website. 
	 *
	 * It determines the active theme background color. It checks if there's a color stored in local storage. 
	 * If not, it falls back to the background color of an element with the class 'theme_colors' and id 'active'.
	 * It then creates two copies of this color: one for the general background and another for the content background.
	 * Depending on whether the active theme color is dark or light, it adjusts these colors differently.
	 * 
	 * For a dark theme, it lightens the content background and brightens the general background.
	 * For a light theme, it darkens both slightly.	
	 * Next, it creates transparent versions of the navigation background color with different opacity levels 
	 * which are used for the overlay transparency in the html header.

	 * Finally, it sets a text color, again checking local storage first before falling back to the color of the active theme element.

	 * The tinycolor library was used to manipulate colors easily. 
	 * This library allows for operations like lightening, darkening, and changing opacity of colors.
	*/
	if (localStorage.getItem('active_theme_bg_color') !== null) {
		active_theme_bg_color = tinycolor(localStorage.getItem('active_theme_bg_color'));
	} else {
		active_theme_bg_color = tinycolor(document.querySelector('.theme_colors > #active').style.backgroundColor);
	}
	bg_color = active_theme_bg_color.clone();
	content_bg_color = active_theme_bg_color.clone();

	if (active_theme_bg_color.isDark()) {
		document.documentElement.style.setProperty('--nav_bg_color', active_theme_bg_color.toString());
		document.documentElement.style.setProperty('--content_bg_color', content_bg_color.lighten(10).toString());
		document.documentElement.style.setProperty('--bg_color', bg_color.brighten(20).toString());
	} else {
		document.documentElement.style.setProperty('--nav_bg_color', active_theme_bg_color.darken(20).toString());
		document.documentElement.style.setProperty('--content_bg_color', content_bg_color.darken(5).toString());
		document.documentElement.style.setProperty('--bg_color', bg_color.toString());
	}
	nav_bg_color_transparent = active_theme_bg_color.clone();
	document.documentElement.style.setProperty(
		'--nav_bg_color_transparent',
		nav_bg_color_transparent.setAlpha(0.4).toString()
	);
	document.documentElement.style.setProperty(
		'--nav_bg_color_transparent_2',
		nav_bg_color_transparent.setAlpha(0.5).toString()
	);

	if (localStorage.getItem('text_color') !== null) {
		text_color = tinycolor(localStorage.getItem('text_color'));
	} else {
		text_color = tinycolor(document.querySelector('.theme_colors > #active').style.color);
	}
	document.documentElement.style.setProperty('--text_color', text_color.toString());
}

function reassign_id_and_aria_selected(element) {
	/**
	 * Reassigns the 'id' and 'aria-selected' attributes of the active theme color element.
	 *
	 * This function is used reassign active id and to update accessibility state of the active theme color
	 * when the user clicks on a different theme color.
	 *
	 * @param {HTMLElement} element - The new active theme color element.
	 */
	prev_active_element = document.querySelector('.theme_colors > #active');
	prev_active_element.removeAttribute('id');
	prev_active_element.removeAttribute('aria-selected');
	element.id = 'active';
	element.setAttribute('aria-selected', true);
}

// Initializes the theme color selection functionality on the page.
let theme_colors = document.querySelectorAll('.theme_colors > div');
let active_element_detected = false;

if (localStorage.getItem('active_theme_bg_color') === null) {
	// logic for displaying the active theme color and retain the colour in the local storage
	// to make it persistent across different pages of the web site and hiding the inactive ones.
	for (let i = 0; i < theme_colors.length; i++) {
		if (theme_colors[i].id != 'active') {
			theme_colors[i].style.display = 'none';
		} else {
			localStorage.setItem('active_theme_bg_color', theme_colors[i].style.backgroundColor);
		}
	}
} else {
	// when a page is loaded, if a theme color exists in the local storage, then display the div associated to
	// the active theme color and hide others.
	for (let i = 0; i < theme_colors.length; i++) {
		if (theme_colors[i].style.backgroundColor == localStorage.getItem('active_theme_bg_color')) {
			reassign_id_and_aria_selected(theme_colors[i]);
			active_element_detected = true;
		} else {
			theme_colors[i].style.display = 'none';
		}
	}
	// if not stored theme color is found, then use the theme color of default div with id set to
	// active for the page display and store it in the local storage.
	if (!active_element_detected) {
		active_div = document.querySelector('.theme_colors > #active');
		active_div.style.display = 'block';
		localStorage.setItem('active_theme_bg_color', active_div.style.backgroundColor);
		active_element_detected = false;
	}
}

for (let i = 0; i < theme_colors.length; i++) {
	theme_colors[i].addEventListener('click', function () {
		// Set a local storage variables with the theme colors information
		localStorage.setItem('active_theme_bg_color', this.style.backgroundColor);
		localStorage.setItem('text_color', this.style.color);

		//hide all divs and show only the active one and change the order of the divs accordingly.
		let previous_active_order = document.querySelector('.theme_colors > #active').style.order;
		let this_order = this.style.order;
		reassign_id_and_aria_selected(this);

		for (let i = 0; i < theme_colors.length; i++) {
			//hide div if previously unhidden and is not the active div
			if (theme_colors[i].id != 'active' && theme_colors[i].style.display != 'none') {
				theme_colors[i].style.display = 'none';
				//if div was previously the active one, change the order number to that of the new active div.
				if (theme_colors[i].style.order == parseInt(previous_active_order)) {
					theme_colors[i].style.order = parseInt(this_order);
				}
			} else {
				theme_colors[i].style.display = 'block';
				//identity the last div in the list and assign the order of the active div to it
				if (theme_colors[i].style.order == theme_colors.length) {
					theme_colors[i].style.order = parseInt(this_order);
				}
			}
		}
		document.querySelector('.theme_colors > #active').style.order = theme_colors.length;

		change_theme();
	});

	// This code enables keyboard navigation for theme color selection, allowing
	// users to activate a theme change by pressing Enter on a focused color element.
	theme_colors[i].addEventListener('keydown', function (event) {
		if (event.key === 'Enter') {
			theme_colors[i].click(); // Simulate a click event
		}
	});
	//assign the flex order property to the list of divs
	theme_colors[i].style.order = i + 1;
}

change_theme();
