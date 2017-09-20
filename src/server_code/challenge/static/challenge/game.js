$(function() {
    // When we're using HTTPS, use WSS too.
    // var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    const turnSpeed = 300;  // ms
    var canvas = document.getElementById('mainCanvas');
    var ctx = canvas.getContext("2d");
    const codes = [cop_code, robber_code];
    codes.sort();
    const baseUrl = "/challenge/game/" + codes[0] + "/" + codes[1] + "/";
    const gameUrl = httpHost + baseUrl;
    const wsUrl = wsHost + baseUrl;
    var maze = {
      rows: 0,
      cols: 0,
      nodes: null,
    };


    function drawMaze(maze, canvas) {
      // canvas.width = maze.cols * 30;
      // canvas.height = maze.rows * 30;
      console.log(maze);
      maze.nodes.forEach(function(col) {
        col.forEach(function(node) {
          var img = new Image(30, 30);
          img.src = images_url + node.img;
          const col = node.coordinates.split(":")[0];
          const row = node.coordinates.split(":")[1];
          const x = col * 30;
          const y = row * 30;
          img.onload = function() {
            ctx.drawImage(img, x, y);
          };
        });
      });
    };

    class Bank {
      constructor(id, coordinates) {
        this.id = id;
        this.is_visible = true;
        this.coordinates = coordinates;
        this.col = coordinates.split(':')[0];
        this.row = coordinates.split(':')[1];
        this.img = 'coinstack.png';
        this.animationDirection = "up";

        // Construct and place in canvas.
        var div = document.createElement('div');
        div.id = "bank_div_" + this.id;
        div.style.position = 'absolute';
        div.style.left = this.col * 30 + 'px';
        div.style.top = this.row * 30 + 'px';
        var canvas = document.createElement('canvas');
        canvas.id = 'bank_canvas_' + this.id;
        canvas.width = 30;
        canvas.height = 30;
        $('.game').append(div);

        // Save div and canvas context to object. Paint.
        this.wrapper = $('#' + div.id);  // convert to a JQuery object for animation.
        this.wrapper.append(canvas)
        this.ctx = canvas.getContext('2d');
        this.paint(this.img);
      }

      paint(imgName) {
        var canvasCtx = this.ctx;
        var img = new Image(30, 30);
        img.src = images_url + imgName;
        img.onload = function() {
          canvasCtx.drawImage(img, 0, 0);
        };
      }

      shuffle() {
        if (this.animationDirection == "up") {
          this.animationDirection = "down";
          this.wrapper.animate({ 'top': '-=10px' }, { duration: turnSpeed, queue: false });
        } else {
          this.wrapper.animate({ 'top': '+=10px' }, { duration: turnSpeed, queue: false });
          this.animationDirection = "up";
        }
      }

      show() {
          console.log("Showing bank.");
          this.is_visible = true;
          this.paint(this.img);
      }

      hide() {
          console.log("Hiding bank");
          this.is_visible = false;
          this.ctx.clearRect(0, 0, 30, 30);
      }

    }

    class Player {
        constructor(wrapper, canvas) {
            this.id = 0;
            this.row = 0;
            this.col = 0;
            this.color = 'red';
            this.canvas = canvas;
            this.wrapper = wrapper;
            this.ctx = canvas.getContext('2d');
        }

        changeColor() {
            if (this.color == this.primaryColor) {
              this.color = this.secondaryColor;
            } else {
              this.color = this.primaryColor;
            }
            this.ctx.clearRect(0, 0, 30, 30);
            this.ctx.beginPath();
            const radius = 10;
            const centerX = 15;
            const centerY = 15;
            this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI, false);
            this.ctx.fillStyle = this.color;
            this.ctx.fill();
        }

        move(new_position) {
            var col = new_position.split(':')[0];
            var row = new_position.split(':')[1];
            this.col = col;
            this.row = row;
            var x = col * 30;
            var y = row * 30;
            this.wrapper.animate({ 'top': y + 'px', 'left': x + 'px' },  { duration: turnSpeed, queue: false });
        }

        removeFromElementFromCanvas() {
            console.log("Removing player");
            this.wrapper.remove();
        }
    }  // End Player

    class Robber extends Player {
        constructor(wrapper, canvas) {
            super(wrapper, canvas);
            this.primaryColor = 'yellow';
            this.secondaryColor = 'yellow';
            this.color = this.primaryColor;
            this.getawayMode = false;
        }

        enterGetAwayMode() {
          console.log("Entering getaway mode");
          this.getawayMode = true;
          this.primaryColor = 'red';
          this.secondaryColor = 'yellow';
        }
    }  // End Robber

    class Cop extends Player {
        constructor(wrapper, canvas) {
            super(wrapper, canvas);
            this.primaryColor = 'red';
            this.secondaryColor = 'blue';
            this.color = this.primaryColor;
        }
    }  // End Cop


    // Game objects
    cops = [];
    robbers = [];
    banks = [];

    function placePlayers(coordinates, teamType) {
      var players = []
      console.log("In place players");
      for (i = 0; i < coordinates.length; i++) {
        var coord = coordinates[i];
        if (coord == null) {
          continue;
        }
        var col = coord.split(':')[0];
        var row = coord.split(':')[1];
        var div = document.createElement('div');
        div.id = teamType + "_div_" + i;
        div.style.position = 'absolute';
        div.style.left = col * 30 + 'px';
        div.style.top = row * 30 + 'px';
        var canvas = document.createElement('canvas');
        canvas.id = teamType + '_canvas_' + i;
        canvas.width = 30;
        canvas.height = 30;
        $('.game').append(div);
        div = $('#' + div.id);  // convert to a JQuery object for animation.
        if (teamType == "COPS") {
          cops.push(new Cop(div, canvas));
        } else {
          robbers.push(new Robber(div, canvas));
        }
        div.append(canvas)
      }
    }

    function placeBanks(bank_coordinates) {
      for (var i = 0; i < bank_coordinates.length; i++) {
        if (bank_coordinates[i] != null) {
          banks.push(new Bank(i, bank_coordinates[i]));
        }
      }
    }

    // Get the maze
    $.getJSON(gameUrl, function(data) {
      maze.rows = data.rows;
      maze.cols = data.cols;
      maze.nodes = data.maze;
      drawMaze(maze, canvas);
      console.log(data);
      placePlayers(data.COPS.players, "COPS");
      placePlayers(data.ROBBERS.players, "ROBBERS");
      if ('banks' in data) {
        console.log("Placing banks");
        placeBanks(data.banks);
      } else {
        console.error('Banks not found in inital game data!');
      }

    });


    // Animation loop
    setInterval(function() {
        for(var i = 0; i < cops.length; i++){
            if (cops[i] != null) {
                cops[i].changeColor();
            }
        }
        for(var i = 0; i < robbers.length; i++){
            if (robbers[i] != null) {
                robbers[i].changeColor();
            }
        }
        for(var i = 0; i < banks.length; i++) {
            if (banks[i] != null) {
                banks[i].shuffle();
            }
        }
    }, 500);


    // START EVENTS MANAGEMENT HERE. GAME LOGIC TOO.

    var chatsock = new ReconnectingWebSocket(wsUrl);
    var time;

    chatsock.onmessage = function(message) {
        var data = JSON.parse(message.data);
        console.log(data);
        if ("positions" in data) {
          // On receipt of moves from the server.
          // Go through the players and move them.
          var positions = data.positions;
          if ("COPS" in positions) {
            positions = positions.COPS;
            for(var i = 0; i < cops.length; i++) {
              if (positions[i] != null && robbers[i] != null) {
                console.log('Moving COP ' + positions[i]);
                cops[i].move(positions[i]);
              }
            }
          } else {
            positions = positions.ROBBERS;
            for(var i = 0; i < robbers.length; i++) {
              if (positions[i] != null && robbers[i] != null) {
                console.log('Moving ROBBER ' + positions[i]);
                robbers[i].move(positions[i]);
              }
            }
          }
        }  // End movements if
        if ('events' in data) {
            events = data.events;
            for (e of events) {
                console.log(e.event);
                $('#event').text(e.event);
                if (e.event == 'GAME OVER') {
                    console.log(e.actions[0]);  // Report the winning team.
                    // Disconnect the socket.
                    chatsock.close();
                    chatsock = null;
                }
                for (var action_str of e.actions) {
                  console.log(action_str);
                    // Take any necessary UI action based on the event.
                    var actions = action_str.split(' ');
                    switch(actions[0]) {
                        case "REMOVE":
                            var team_arr;
                            if (actions[1] == "ROBBERS") {
                                team_arr = robbers;
                            } else if (actions[1] == "COPS") {
                                team_arr = cops;
                            } else {
                                console.error("Unknown entity " + actions[1]);
                                continue;
                            }
                            // Get player index. Delete their elements. Remove from array.
                            const player_idx = actions[2];
                            if (player_idx == -1) {
                                console.error("Can't find player with coordinates given in event!");
                                continue;
                            }
                            team_arr[player_idx].removeFromElementFromCanvas();
                            team_arr[player_idx] = null;
                            break;
                        case "HIDE":
                            if (actions[1] == "BANK") {
                                const bank_idx = actions[2];
                                banks[bank_idx].hide();
                            } else {
                                console.error("Unknown entity to HIDE: " + actions[1]);
                                continue;
                            }
                            break;
                        case "SHOW":
                            if (actions[1] == "BANK") {
                                const bank_idx = actions[2];
                                if (bank_idx == -1) {
                                    console.error("Cannot find bank with coordinates given in event!");
                                    continue;
                                }
                                banks[bank_idx].show();

                            } else {
                                console.error("Unknown entity to HIDE: " + actions[1]);
                                continue;
                            }
                            break;
                        case "COLOR":
                          if (actions[1] == "ROBBERS") {
                            // A robber has robbed a bank. Change their colors.
                            const robber_id = actions[2];
                            robbers[robber_id].enterGetAwayMode();
                          }
                          break;
                    }

                }
            }
        } // End if events
        if ('cop_score' in data) {
            $('#cop-score').text(data.cop_score);
        }
        if ('robber_score' in data) {
            $('#robber-score').text(data.robber_score);
        }

    };




    // $("#chatform").on("submit", function(event) {
    //     var message = {
    //         handle: $('#handle').val(),
    //         message: $('#message').val(),
    //     }
    //     chatsock.send(JSON.stringify(message));
    //     $("#message").val('').focus();
    //     return false;
    // });
});
