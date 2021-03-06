"""
Crypto Algorithms for the Helios Voting System

FIXME: improve random number generation.

Ben Adida
ben@adida.net
"""

import math, sha, logging
from referenda.crypto import randpool, number

import numtheory

# some utilities
class Utils:
    RAND = randpool.RandomPool()
    
    @classmethod
    def random_seed(cls, data):
        cls.RAND.add_event(data)
    
    @classmethod
    def random_mpz(cls, n_bits):
        low = 2**(n_bits-1)
        high = low * 2
        
        # increment and find a prime
        # return randrange(low, high)

        return number.getRandomNumber(n_bits, cls.RAND.get_bytes)
    
    @classmethod
    def random_mpz_lt(cls, max):
        # return randrange(0, max)
        n_bits = int(math.floor(math.log(max, 2)))
        return (number.getRandomNumber(n_bits, cls.RAND.get_bytes) % max)
    
    @classmethod
    def random_prime(cls, n_bits):
        return number.getPrime(n_bits, cls.RAND.get_bytes)
    
    @classmethod
    def is_prime(cls, mpz):
        #return numtheory.miller_rabin(mpz)
        return number.isPrime(mpz)

    @classmethod
    def xgcd(cls, a, b):
        """
        Euclid's Extended GCD algorithm
        """
        mod = a%b

        if mod == 0:
            return 0,1
        else:
            x,y = cls.xgcd(b, mod)
            return y, x-(y*(a/b))

    @classmethod
    def inverse(cls, mpz, mod):
        # return cls.xgcd(mpz,mod)[0]
        return number.inverse(mpz, mod)
  
    @classmethod
    def random_safe_prime(cls, n_bits):
      p = None
      q = None
      
      while True:
        p = cls.random_prime(n_bits)
        q = (p-1)/2
        if cls.is_prime(q):
          return p

    @classmethod
    def random_special_prime(cls, q_n_bits, p_n_bits):
        p = None
        q = None

        z_n_bits = p_n_bits - q_n_bits

        q = cls.random_prime(q_n_bits)
        
        while True:
            z = cls.random_mpz(z_n_bits)
            p = q*z + 1
            if cls.is_prime(p):
                return p, q, z


class ElGamal:
    def __init__(self):
      self.p = None
      self.q = None
      self.g = None

    @classmethod
    def generate(cls, n_bits):
      """
      generate an El-Gamal environment. Returns an instance
      of ElGamal(), with prime p, group size q, and generator g
      """
      
      EG = ElGamal()
      
      # find a prime p such that (p-1)/2 is prime q
      EG.p = Utils.random_safe_prime(n_bits)

      # q is the order of the group
      EG.q = (EG.p-1)/2
  
      # find g that generates the q-order subgroup
      while True:
        EG.g = Utils.random_mpz_lt(EG.p)
        if pow(EG.g, EG.q, EG.p) == 1:
          break

      return EG

    def generate_keypair(self):
      """
      generates a keypair in the setting
      """
      
      keypair = EGKeyPair()
      keypair.generate(self.p, self.g)
  
      return keypair
      
    def toJSONDict(self):
      return {'p': str(self.p), 'q': str(self.q), 'g': str(self.g)}
      
    @classmethod
    def fromJSONDict(cls, d):
      eg = cls()
      eg.p = int(d['p'])
      eg.q = int(d['q'])
      eg.g = int(d['g'])
      return eg

class EGKeyPair:
    def __init__(self):
      self.pk = EGPublicKey()
      self.sk = EGSecretKey()

    def generate(self, p, g):
      """
      Generate an ElGamal keypair
      """
      self.pk.g = g
      self.pk.p = p
      self.pk.q = (p-1)/2
      
      self.sk.x = Utils.random_mpz_lt(p)
      self.pk.y = pow(g, self.sk.x, p)
      
      self.sk.pk = self.pk

class EGPublicKey:
    def __init__(self):
        self.y = None
        self.p = None
        self.g = None
        self.q = None

    def encrypt_with_r(self, plaintext, r, encode_message= False):
        """
        expecting plaintext.m to be a big integer
        """
        ciphertext = EGCiphertext()
        ciphertext.pk = self

        # make sure m is in the right subgroup
        if encode_message:
          y = plaintext.m + 1
          if pow(y, self.q, self.p) == 1:
            m = y
          else:
            m = -y % self.p
        else:
          m = plaintext.m
        
        ciphertext.alpha = pow(self.g, r, self.p)
        ciphertext.beta = (m * pow(self.y, r, self.p)) % self.p
        
        return ciphertext

    def encrypt_return_r(self, plaintext):
        """
        Encrypt a plaintext and return the randomness just generated and used.
        """
        r = Utils.random_mpz_lt(self.q)
        ciphertext = self.encrypt_with_r(plaintext, r)
        
        return [ciphertext, r]

    def encrypt(self, plaintext):
        """
        Encrypt a plaintext, obscure the randomness.
        """
        return self.encrypt_return_r(plaintext)[0]
        
    def to_dict(self):
        """
        Serialize to dictionary.
        """
        return {'y' : str(self.y), 'p' : str(self.p), 'g' : str(self.g) , 'q' : str(self.q)}

    toJSONDict = to_dict

    @classmethod
    def from_dict(cls, d):
        """
        Deserialize from dictionary.
        """
        pk = cls()
        pk.y = int(d['y'])
        pk.p = int(d['p'])
        pk.g = int(d['g'])
        pk.q = int(d['q'])
        return pk
        
    fromJSONDict = from_dict

class EGSecretKey:
    def __init__(self):
        self.x = None
        self.pk = None
        
    def decrypt(self, ciphertext, decode_m=False):
        """
        Decrypt a ciphertext. Optional parameter decides whether to encode the message into the proper subgroup.
        """
        m = (Utils.inverse(pow(ciphertext.alpha, self.x, self.pk.p), self.pk.p) * ciphertext.beta) % self.pk.p

        if decode_m:
          # get m back from the q-order subgroup
          if m < self.pk.q:
            y = m
          else:
            y = -m % self.pk.p

          return EGPlaintext(y-1, self.pk)
        else:
          return EGPlaintext(m, self.pk)

    def prove_decryption(self, ciphertext):
        """
        given g, y, alpha, beta/(encoded m), prove equality of discrete log
        with Chaum Pedersen, and that discrete log is x, the secret key.

        Prover sends a=g^w, b=alpha^w for random w
        Challenge c = sha1(a,b) with and b in decimal form
        Prover sends t = w + xc

        Verifier will check that g^t = a * y^c
        and alpha^t = b * beta/m ^ c
        """
        
        m = (Utils.inverse(pow(ciphertext.alpha, self.x, self.pk.p), self.pk.p) * ciphertext.beta) % self.pk.p
        beta_over_m = (ciphertext.beta * Utils.inverse(m, self.pk.p)) % self.pk.p

        # pick a random w
        w = Utils.random_mpz_lt(self.pk.q)
        a = pow(self.pk.g, w, self.pk.p)
        b = pow(ciphertext.alpha, w, self.pk.p)

        c = int(sha.new(str(a) + "," + str(b)).hexdigest(),16)

        t = (w + self.x * c) % self.pk.q

        return m, {
            'commitment' : {'A' : str(a), 'B': str(b)},
            'challenge' : str(c),
            'response' : str(t)
          }

    def to_dict(self):
        return {'x' : str(self.x), 'pk' : self.pk.to_dict()}
        
    toJSONDict = to_dict

    @classmethod
    def from_dict(cls, d):
        if not d:
          return None
          
        sk = cls()
        sk.x = int(d['x'])
        sk.pk = EGPublicKey.from_dict(d['pk'])
        return sk
        
    fromJSONDict = from_dict

class EGPlaintext:
    def __init__(self, m = None, pk = None):
        self.m = m
        self.pk = pk
        
    def to_dict(self):
        return {'m' : self.m}

    @classmethod
    def from_dict(cls, d):
        r = cls()
        r.m = d['m']
        return r
   

class EGCiphertext:
    def __init__(self, alpha=None, beta=None, pk=None):
        self.pk = pk
        self.alpha = alpha
        self.beta = beta

    def __mul__(self,other):
        """
        Homomorphic Multiplication of ciphertexts.
        """
        if type(other) == int and (other == 0 or other == 1):
          return self
          
        if self.pk != other.pk:
          logging.info(self.pk)
          logging.info(other.pk)
          raise Exception('different PKs!')
        
        new = EGCiphertext()
        
        new.pk = self.pk
        new.alpha = (self.alpha * other.alpha) % self.pk.p
        new.beta = (self.beta * other.beta) % self.pk.p

        return new
  
    def reenc_with_r(self, r):
        """
        We would do this homomorphically, except
        that's no good when we do plaintext encoding of 1.
        """
        new_c = EGCiphertext()
        new_c.alpha = (self.alpha * pow(self.pk.g, r, self.pk.p)) % self.pk.p
        new_c.beta = (self.beta * pow(self.pk.y, r, self.pk.p)) % self.pk.p
        new_c.pk = self.pk

        return new_c
    
    def reenc_return_r(self):
        """
        Reencryption with fresh randomness, which is returned.
        """
        r = Utils.random_mpz_lt(self.pk.q)
        new_c = self.reenc_with_r(r)
        return [new_c, r]
    
    def reenc(self):
        """
        Reencryption with fresh randomness, which is kept obscured (unlikely to be useful.)
        """
        return self.reenc_return_r()[0]
    
    def __eq__(self, other):
      """
      Check for ciphertext equality.
      """
      if other == None:
        return False
        
      return (self.alpha == other.alpha and self.beta == other.beta)
    
    def generate_encryption_proof(self, plaintext, randomness, challenge_generator):
      """
      Generate the disjunctive encryption proof of encryption
      """
      # random W
      w = Utils.random_mpz_lt(self.pk.q)

      # build the proof
      proof = EGZKProof()

      # compute A=g^w, B=y^w
      proof.commitment['A'] = pow(self.pk.g, w, self.pk.p)
      proof.commitment['B'] = pow(self.pk.y, w, self.pk.p)

      # generate challenge
      proof.challenge = challenge_generator(proof.commitment);

      # Compute response = w + randomness * challenge
      proof.response = (w + (randomness * proof.challenge)) % self.pk.q;

      return proof;
      
    def simulate_encryption_proof(self, plaintext, challenge=None):
      # generate a random challenge if not provided
      if not challenge:
        challenge = Utils.random_mpz_lt(self.pk.q)
        
      proof = EGZKProof()
      proof.challenge = challenge

      # compute beta/plaintext, the completion of the DH tuple
      beta_over_plaintext =  (self.beta * Utils.inverse(plaintext.m, self.pk.p)) % self.pk.p
      
      # random response, does not even need to depend on the challenge
      proof.response = Utils.random_mpz_lt(self.pk.q);

      # now we compute A and B
      proof.commitment['A'] = (Utils.inverse(pow(self.alpha, proof.challenge, self.pk.p), self.pk.p) * pow(self.pk.g, proof.response, self.pk.p)) % self.pk.p
      proof.commitment['B'] = (Utils.inverse(pow(beta_over_plaintext, proof.challenge, self.pk.p), self.pk.p) * pow(self.pk.y, proof.response, self.pk.p)) % self.pk.p

      return proof
    
    def generate_disjunctive_encryption_proof(self, plaintexts, real_index, randomness, challenge_generator):
      # note how the interface is as such so that the result does not reveal which is the real proof.

      proofs = [None for p in plaintexts]

      # go through all plaintexts and simulate the ones that must be simulated.
      for p_num in range(len(plaintexts)):
        if p_num != real_index:
          proofs[p_num] = self.simulate_encryption_proof(plaintexts[p_num])

      # the function that generates the challenge
      def real_challenge_generator(commitment):
        # set up the partial real proof so we're ready to get the hash
        proofs[real_index] = EGZKProof()
        proofs[real_index].commitment = commitment

        # get the commitments in a list and generate the whole disjunctive challenge
        commitments = [p.commitment for p in proofs]
        disjunctive_challenge = challenge_generator(commitments);

        # now we must subtract all of the other challenges from this challenge.
        real_challenge = disjunctive_challenge
        for p_num in range(len(proofs)):
          if p_num != real_index:
            real_challenge = real_challenge - proofs[p_num].challenge

        # make sure we mod q, the exponent modulus
        return real_challenge % self.pk.q
        
      # do the real proof
      real_proof = self.generate_encryption_proof(plaintexts[real_index], randomness, real_challenge_generator)

      # set the real proof
      proofs[real_index] = real_proof

      return EGZKDisjunctiveProof(proofs)
      
    def verify_encryption_proof(self, plaintext, proof):
      """
      Checks for the DDH tuple g, y, alpha, beta/plaintext.
      (PoK of randomness r.)
      
      Proof contains commitment = {A, B}, challenge, response
      """
      
      # check that g^response = A * alpha^challenge
      first_check = (pow(self.pk.g, proof.response, self.pk.p) == ((pow(self.alpha, proof.challenge, self.pk.p) * proof.commitment['A']) % self.pk.p))
      
      # check that y^response = B * (beta/m)^challenge
      beta_over_m = (self.beta * Utils.inverse(plaintext.m, self.pk.p)) % self.pk.p
      second_check = (pow(self.pk.y, proof.response, self.pk.p) == ((pow(beta_over_m, proof.challenge, self.pk.p) * proof.commitment['B']) % self.pk.p))
      
      # print "1,2: %s %s " % (first_check, second_check)
      return (first_check and second_check)
    
    def verify_disjunctive_encryption_proof(self, plaintexts, proof, challenge_generator):
      """
      plaintexts and proofs are all lists of equal length, with matching.
      
      overall_challenge is what all of the challenges combined should yield.
      """
      for i in range(len(plaintexts)):
        # if a proof fails, stop right there
        if not self.verify_encryption_proof(plaintexts[i], proof.proofs[i]):
          print "bad proof %s, %s, %s" % (i, plaintexts[i], proof.proofs[i])
          return False
          
      # logging.info("made it past the two encryption proofs")
          
      # check the overall challenge
      return (challenge_generator([p.commitment for p in proof.proofs]) == (sum([p.challenge for p in proof.proofs]) % self.pk.q))
      
    def verify_decryption_proof(self, plaintext, proof):
      """
      Checks for the DDH tuple g, alpha, y, beta/plaintext
      (PoK of secret key x.)
      """
      return False

    def to_dict(self):
        return {'alpha': str(self.alpha), 'beta': str(self.beta)}

    toJSONDict= to_dict

    def to_string(self):
        return "%s,%s" % (self.alpha, self.beta)
    
    @classmethod
    def from_dict(cls, d, pk = None):
        result = cls()
        result.alpha = int(d['alpha'])
        result.beta = int(d['beta'])
        result.pk = pk
        return result
        
    fromJSONDict = from_dict
    
    @classmethod
    def from_string(cls, str):
        """
        expects alpha,beta
        """
        split = str.split(",")
        return cls.from_dict({'alpha' : split[0], 'beta' : split[1]})

class EGZKProof:
  def __init__(self):
    self.commitment = {'A':None, 'B':None}
    self.challenge = None
    self.response = None
  
  @classmethod
  def from_dict(cls, d):
    p = cls()
    p.commitment = {'A': int(d['commitment']['A']), 'B': int(d['commitment']['B'])}
    p.challenge = int(d['challenge'])
    p.response = int(d['response'])
    return p
    
  def to_dict(self):
    return {
      'commitment' : {'A' : str(self.commitment['A']), 'B' : str(self.commitment['B'])},
      'challenge': str(self.challenge),
      'response': str(self.response)
    }
  
  toJSONDict = to_dict
  
class EGZKDisjunctiveProof:
  def __init__(self, proofs = None):
    self.proofs = proofs
  
  @classmethod
  def from_dict(cls, d):
    dp = cls()
    dp.proofs = [EGZKProof.from_dict(p) for p in d]
    return dp
    
  def to_dict(self):
    return [p.to_dict() for p in self.proofs]
  
  toJSONDict = to_dict

def EG_disjunctive_challenge_generator(commitments):
  array_to_hash = []
  for commitment in commitments:
    array_to_hash.append(str(commitment['A']))
    array_to_hash.append(str(commitment['B']))

  string_to_hash = ",".join(array_to_hash)
  return int(sha.new(string_to_hash).hexdigest(),16)

