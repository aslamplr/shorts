	//Short Data Model
	function Short(data) {
		this.id = ko.observable(data.id);
		this.title_ = data.details.title_;
		this.pub_on = data.details.pub_on;
		this.desc_ = data.details.desc_;
		this.cat_ = data.details.cat_;
		this.tags_ = data.details.tags_;
		this.w_url = data.details.w_url;
		this.f_url = data.details.f_url;
		this.duration = data.details.duration;
		this.d_hhmmss = data.d_hhmmss;
		this.v_cnt = data.details.v_cnt;
		this.v_rating = data.details.v_rating;
		this.alt_fmt_ = data.details.alt_fmt_;
		this.th_nail_url = data.details.th_nail_url;
		this.src = data.details.src;
	};
	// Data model functions
	function getShortWithID(id,shorts) {
		for(var i=0; i<shorts.length; i++){
			if(shorts[i].id() == id){
				return shorts[i];
			}
		}
		return null;
	};
	//Short View Model
	function shortsViewModel() {
		var self = this ;
		self.shorts = ko.observable([]);
		self.chosenShort = ko.observable();
		self.chosenShortID = ko.observable();
		self.ShortsListVisible = ko.observable(true);
		self.ShortsListName = ko.observable('Featured');
		self.dropdownList = ko.observableArray();
		//Adding default items to the dropdown list --
		self.dropdownList.push({name:'YouTube Crawler List'});
		self.dropdownList.push({name:'All List'});
		//post/put back
		self.save = function(short) {
			$.ajax("/tasks", {
				data: ko.toJSON({ short: short }),
				type: "post", contentType: "application/json",
				success: function(result) { alert(result) }
			});
		};
		//Get all shorts
		self.getList = function(listName,start,end) {
			start = typeof start !== 'undefined' ? start : true;
			end = typeof end !== 'undefined' ? end : false;
			//listName = typeof listName !== 'undefined' ? listName : 'Featured';
			console.debug('Getting... list - '+listName);
			if(start && !end){
				$.getJSON("/shorts/list/?knockout=True&name="+listName, function(allData) {
					var mappedShorts = $.map(allData.shorts, function(item) { return new Short(item) });
					self.shorts(mappedShorts);
				});
			}else{
				console.debug(start+':'+end);
				$.getJSON("/shorts/list/"+start+"-"+end+"?knockout=True&name="+listName, function(allData) {
					var mappedShorts = $.map(allData.shorts, function(item) { return new Short(item) });
					all_in_shorts = self.shorts();
					all_in_shorts.push.apply(all_in_shorts, mappedShorts);
					self.shorts(all_in_shorts);
				});
			}
		};
		self.getList(self.ShortsListName()); //To initialize shorts list
		//behaviours
		self.lightsSwitch = function(on) {
			on = typeof on !== 'undefined' ? on : true;
			if(on && $('body').css('background-color') == 'rgb(255, 255, 255)'){
				$('#selectedVideo').css('background-color','#333');
				$('#lightSwText').text('Lights On!');
				$('body').css('background-color','#222');
			}else{
				$('body').css('background-color','#FFFFFF');
				$('#lightSwText').text('Lights Off!');
				$('#selectedVideo').css('background-color','#FFFFFF');
			};
		};
		$(window).scroll(function() {
			if (self.ShortsListVisible() && $(window).scrollTop() == $(document).height() - $(window).height()) {
				shorts_len = self.shorts().length;
				self.getList(self.ShortsListName(),shorts_len+1,shorts_len+11);
			}
		});
		self.changeShortsList = function (dropDownEntry) {
			self.dropdownList.push({name:self.ShortsListName()});
			self.dropdownList.remove(dropDownEntry);
			self.ShortsListName(dropDownEntry.name);
			self.openShortsList();
		};		
		self.openShort = function (short) {
			location.hash = 'shorts/' + short.id();
			self.chosenShortID(short.id());
			console.debug('location hash - '+location.hash);
		};
		self.openShortsList = function () {
			location.hash = 'shorts/list/'+self.ShortsListName();
			console.debug('location hash - '+location.hash);
		};
		//client-side routes using Sammy
		Sammy(function() {
			this.get('#shorts/:chosenShortID', function(){
				id = this.params.chosenShortID;
				selectedShort = getShortWithID(id,self.shorts());
				if (selectedShort){
					self.chosenShort(selectedShort);
					self.ShortsListVisible(false);
				};
			});
			this.get('#shorts/list/:ShortsListName', function(){
				self.lightsSwitch(false);
				shortsListName = this.params.ShortsListName;
				self.getList(shortsListName);
				self.chosenShortID(null);
				self.chosenShort(null);
				self.ShortsListVisible(true);
			});
			/*this.get('', function(){
				self.lightsSwitch(false);
			});*/
		}).run();
	}
	//Binding
	ko.applyBindings(new shortsViewModel());