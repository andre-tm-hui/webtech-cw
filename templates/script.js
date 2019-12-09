var url = window.location.href;

function login() {
	console.out.prinln("yeet")
	userid = $("#userid").val()
	if(userid) {
		$.get(url + "login", {"userid":userid}, function(data){
			if (!data) {
				var x = document.getElementById("wronguserid")
				if(x.style.display === "none") {
					s.style.display = "block"
				}
			} 
		})
	}
}