const canvas = document.querySelector('canvas');
const c = canvas.getContext('2d');

canvas.width = 1024;
canvas.height = 576;

c.fillRect(0, 0, canvas.width, canvas.height);

const gravity = 0.7;

class Sprite {
    constructor({ position, velocity, color = "red", offset }) {
        this.position = position;
        this.velocity = velocity;
        this.height = 150;
        this.width = 50;
        this.lastKey;
        this.attackBox = {
            position: {
                x: this.position.x,
                y: this.position.y
            },
            offset,
            width: 100,
            height: 50
        };
        this.color = color;
        this.isAttacking = false;
        this.health = 100;
    }

    draw() {
        c.fillStyle = this.color;
        c.fillRect(this.position.x, this.position.y, this.width, this.height);

        // Draw attack box
        if (this.isAttacking) {
            c.fillStyle = 'green';
            c.fillRect(this.attackBox.position.x, this.attackBox.position.y, this.attackBox.width, this.attackBox.height);
        }
    }

    update() {
        this.draw();
        this.attackBox.position.x = this.position.x + this.attackBox.offset.x;
        this.attackBox.position.y = this.position.y;

        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;

        // Gravity effect
        if (this.position.y + this.height + this.velocity.y >= canvas.height) {
            this.velocity.y = 0;
        } else {
            this.velocity.y += gravity;
        }

        // Prevent sprite from going outside the canvas
        if (this.position.x < 0) {
            this.position.x = 0;
        } else if (this.position.x + this.width > canvas.width) {
            this.position.x = canvas.width - this.width;
        }
    }

    attack() {
        this.isAttacking = true;
        setTimeout(() => {
            this.isAttacking = false;
        }, 100);
    }
}

class EnemyBot extends Sprite {
    constructor({ position, velocity, color = "blue", offset }) {
        super({ position, velocity, color, offset });
        this.attackRange = 100;
        this.attackCooldown = 2000;
        this.lastAttackTime = 0;
        this.speed = 20;
        this.attackDamage = 10; 
    }

    update() {
        
        if (Math.random() < 0.05) {
            this.velocity.x = Math.random() > 0.5 ? this.speed : -this.speed;
        }

        
        const currentTime = Date.now();
        const timeSinceLastAttack = currentTime - this.lastAttackTime;
        if (timeSinceLastAttack >= this.attackCooldown) {
            const distanceToPlayer = Math.abs(player.position.x - this.position.x);
            if (distanceToPlayer < this.attackRange) {
                this.attack();
                this.lastAttackTime = currentTime;
            }
        }

        
        super.update();

        
        if (this.position.x < 0) {
            this.position.x = 0;
        } else if (this.position.x + this.width > canvas.width) {
            this.position.x = canvas.width - this.width;
        }
    }

    attack() {
        if (!this.isAttacking) {
            this.isAttacking = true;
            setTimeout(() => {
                if (rectangularCollision({ rectangle1: this, rectangle2: player })) {
                    player.health -= this.attackDamage;
                    document.querySelector('#playerHealth').style.width = player.health + '%';
                }
                this.isAttacking = false;
            }, 100); 
        }
    }
}

const player = new Sprite({
    position: { x: 0, y: 0 },
    velocity: { x: 0, y: 0 },
    offset: { x: 0, y: 0 }
});

const difficulties = {
    easy: {
        enemySpeed: 5,
        attackCooldown: 3000,
        attackDamage: 5
    },
    normal: {
        enemySpeed: 10,
        attackCooldown: 2000,
        attackDamage: 10
    },
    hard: {
        enemySpeed: 15,
        attackCooldown: 1000,
        attackDamage: 30
    }
};
let currentDifficulty = difficulties.easy;

const enemy = new EnemyBot({
    position: { x: 400, y: 100 },
    velocity: { x: 0, y: 0 },
    color: "blue",
    offset: { x: -50, y: 0 },
    speed: currentDifficulty.enemySpeed,
    attackCooldown: currentDifficulty.attackCooldown,
    attackDamage: currentDifficulty.attackDamage
});

const keys = {
    a: { pressed: false },
    d: { pressed: false },
    w: { pressed: false },
    ArrowRight: { pressed: false },
    ArrowLeft: { pressed: false },
    ArrowUp: { pressed: false }
};

function rectangularCollision({ rectangle1, rectangle2 }) {
    return (
        rectangle1.attackBox.position.x + rectangle1.attackBox.width >= rectangle2.position.x &&
        rectangle1.attackBox.position.x <= rectangle2.position.x + rectangle2.width &&
        rectangle1.attackBox.position.y + rectangle1.attackBox.height >= rectangle2.position.y &&
        rectangle1.attackBox.position.y <= rectangle2.position.y + rectangle2.height
    );
}

function determineWinner({ player, enemy, timerId }) {
    clearTimeout(timerId);
    document.querySelector('#displayText').style.display = 'flex';
    if (player.health === enemy.health) {
        document.querySelector('#displayText').innerHTML = 'Tie';
    } else if (player.health > enemy.health) {
        document.querySelector('#displayText').innerHTML = 'Player 1 Wins';
    } else {
        document.querySelector('#displayText').innerHTML = 'Player 2 Wins';
    }
}

let timer = 60;
let timerId;

function decreaseTimer() {
    if (timer > 0) {
        timerId = setTimeout(decreaseTimer, 1000);
        timer--;
        document.querySelector('#timer').innerHTML = timer;
    } else {
        determineWinner({ player, enemy, timerId });
    }
}

decreaseTimer();

function animate() {
    window.requestAnimationFrame(animate);
    c.fillStyle = 'black';
    c.fillRect(0, 0, canvas.width, canvas.height);

    player.update();
    enemy.update();

    // Player movement
    player.velocity.x = 0;
    if (keys.a.pressed && player.lastKey === 'a') {
        player.velocity.x = -5;
    } else if (keys.d.pressed && player.lastKey === 'd') {
        player.velocity.x = 5;
    }

    
    if (rectangularCollision({ rectangle1: player, rectangle2: enemy }) && player.isAttacking) {
        player.isAttacking = false;
        enemy.health -= 10;
        document.querySelector('#enemyHealth').style.width = enemy.health + '%';
    }

    
    if (rectangularCollision({ rectangle1: enemy, rectangle2: player }) && enemy.isAttacking) {
        enemy.isAttacking = false;
        player.health -= 10;
        document.querySelector('#playerHealth').style.width = player.health + '%';
    }

    // End game
    if (enemy.health <= 0 || player.health <= 0) {
        determineWinner({ player, enemy, timerId });
    }
}

animate();

window.addEventListener('keydown', (event) => {
    switch (event.key) {
        case 'd':
            keys.d.pressed = true;
            player.lastKey = 'd';
            break;
        case 'a':
            keys.a.pressed = true;
            player.lastKey = 'a';
            break;
        case 'w':
            player.velocity.y = -10;
            break;
        case ' ':
            player.attack();
            break;
        case 'ArrowRight':
            keys.ArrowRight.pressed = true;
            enemy.lastKey = 'ArrowRight';
            break;
        case 'ArrowLeft':
            keys.ArrowLeft.pressed = true;
            enemy.lastKey = 'ArrowLeft';
            break;
        case 'ArrowUp':
            enemy.velocity.y = -10;
            break;
        case '0':
            enemy.attack();
            break;
        case '1':
            changeDifficulty('easy');
            break;
        case '2':
            changeDifficulty('normal');
            break;
        case '3':
            changeDifficulty('hard');
            break;
    }
});

window.addEventListener('keyup', (event) => {
    switch (event.key) {
        case 'd':
            keys.d.pressed = false;
            break;
        case 'a':
            keys.a.pressed = false;
            break;
        case 'w':
            keys.w.pressed = false;
            break;
        case 'ArrowRight':
            keys.ArrowRight.pressed = false;
            break;
        case 'ArrowLeft':
            keys.ArrowLeft.pressed = false;
            break;
        case 'ArrowUp':
            keys.ArrowUp.pressed = false;
            break;
    }
});

function changeDifficulty(difficulty) {
    if (difficulties.hasOwnProperty(difficulty)) {
        currentDifficulty = difficulties[difficulty];
        enemy.speed = currentDifficulty.enemySpeed;
        enemy.attackCooldown = currentDifficulty.attackCooldown;
        enemy.attackDamage = currentDifficulty.attackDamage;
        console.log(`Difficulty changed to ${difficulty}`);
        console.log(`Enemy attack damage: ${enemy.attackDamage}`);
        resetGame();
    } else {
        console.log(`Invalid difficulty: ${difficulty}`);
    }
}

function resetGame() {
    player.health = 100;
    enemy.health = 100;
    player.position.x = 0;
    player.position.y = 0;
    enemy.position.x = 400;
    enemy.position.y = 100;
    timer = 60;
    document.querySelector('#timer').innerHTML = timer;
    clearTimeout(timerId);
    decreaseTimer();
}
